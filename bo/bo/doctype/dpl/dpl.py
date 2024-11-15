# -*- coding: utf-8 -*-
# Copyright (c) 2020, Sistem Koperasi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document
from frappe import _, scrub, ValidationError
import frappe, json, os
from six import iteritems, string_types
from frappe.desk.form.load import get_attachments
from frappe.utils import get_hook_method, get_files_path
# from bo.bo.doctype.lpd.exporter import Importer
from bo.bo.utils.exporter import Exporter
from bo.bo.bo_integration.tsj_integration import TSJConnect
from frappe.utils.background_jobs import enqueue
from frappe.utils.csvutils import validate_google_sheets_url
from frappe import _
import requests, textwrap
from frappe.utils.user import get_user_fullname
import re


class DPL(Document):
	def __init__(self, *args, **kwargs):
		super(DPL, self).__init__(*args, **kwargs)

	def validate(self):
			pass

	def before_submit(self):
		if self.distributor == "TSJ":
			conn = TSJConnect()
		else:
			return

		def min_qty(disc):
				if disc > 0:
					return 1
				else:
					return 0
		def max_qty(disc):
				if disc > 0:
					return 99999
				else:
					return 0

		group_ids = [i.item_code for i in self.items]
		items = frappe.db.get_list('Item', fields=['tsj_item_code as productCode', 'group_proid'], filters={'group_proid': ['in', group_ids],'tsj_item_code':['!=', ""]})
		if self.type[0:3] == "DPL":
			group_disc = {int(i.item_code): {"d1":i.total_disc, "d1QtyMin":min_qty(i.total_disc), "d1QtyMax":max_qty(i.total_disc)} for i in self.items}
			for item in items:
				if item['group_proid'] in group_disc:
						item.update({'d1': group_disc[item['group_proid']]['d1'],
												'e1': 0,
												'd1QtyMin': group_disc[item['group_proid']]['d1QtyMin'],
												'd1QtyMax': group_disc[item['group_proid']]['d1QtyMax'],
												'e1QtyMin':0, 'e1QtyMax':0
												})
						# item.pop('group_proid', None)
			# frappe.throw(group_disc)

			# details = [{"ItemCode": i.item_code, "d1":i.total_disc, "D3":0, "d1QtyMin":min_qty(i.total_disc), "d1QtyMax":max_qty(i.total_disc), "D3QtyMin":0, "D3QtyMax":0} for i in self.items]
			res = conn.post_dpl(self.name, self.outid, self.start_date, self.end_date, self.remark, items)
		elif self.type[0:3] == "DPF":
			group_disc = {int(i.item_code): {'productQty': i.qty, 'ItemPrice': i.hna, 'ItemD1': i.total_disc} for i in self.items}
			# details = [{'ItemCode': i.item_code, 'productQty': i.qty, 'ItemPrice': i.hna, 'ItemE1': 0, 'ItemD1': i.total_disc} for i in self.items]
			for item in items:
				if item['group_proid'] in group_disc:
						item.update({'productQty': group_disc[item['group_proid']]['productQty'],
									 			'priceList': '555',
												'discountE1': 0,
												'discountD1': group_disc[item['group_proid']]['ItemD1']
												})
						# item.pop('group_proid', None)
			res = conn.post_dpf(self.name, self.outid, self.approver_1_name, self.approver_2_name, self.remark, items)

		if res["statusCode"] in ["TTPM_CQL_000", "DPF_COR_000"]:
			frappe.msgprint(res["message"])

			if self.distributor == "TSJ":
				if self.type[0:3] == "DPL":
					self.reference = res["data"]["spkNumber"]
				elif self.type[0:3] == "DPF":
					self.reference = res["data"]["dpfNumber"]
		else:
			frappe.throw(res["message"])


	def parseXLS(self):
		file_url = self.get_full_path() # file attachment only the first one attached
		fname = os.path.basename(file_url)
		fxlsx = re.search("^{}.*\.xlsx".format(self.doctype), fname)

		if(fxlsx): # match
			with open( file_url , "rb") as upfile:
				fcontent = upfile.read()
			if frappe.safe_encode(fname).lower().endswith("xlsx".encode('utf-8')):
				from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file
				rows = read_xlsx_file_from_attached_file(fcontent=fcontent)
			columns = rows[0]
			rows.pop(0)
			data = rows
			return {"columns": columns, "data": data}
		else:
			return {"status" : "Error", "filename": fname, "doctype": self.doctype}


	def get_full_path(self):
			"""Returns file path from given file name"""
			att = get_attachments(self.doctype, self.name)
			if att:
				file_path = att[0].file_url or att[0].file_name
			else:
				frappe.throw("No Attachment found")

			if "/" not in file_path:
				file_path = "/files/" + file_path

			if file_path.startswith("/private/files/"):
				file_path = get_files_path(*file_path.split("/private/files/", 1)[1].split("/"), is_private=1)

			elif file_path.startswith("/files/"):
				file_path = get_files_path(*file_path.split("/files/", 1)[1].split("/"))

			else:
				frappe.throw(_("There is some problem with the file url: {0}").format(file_path))

			return file_path

	def validate_import_file(self):
		if self.import_file:
			# validate template
			self.get_importer()

	def validate_google_sheets_url(self):
		if not self.google_sheets_url:
			return
		validate_google_sheets_url(self.google_sheets_url)

	def get_preview_from_template(self, import_file=None, google_sheets_url=None):
		if import_file:
			self.import_file = import_file

		if google_sheets_url:
			self.google_sheets_url = google_sheets_url

		if not (self.import_file or self.google_sheets_url):
			return

		i = self.get_importer()
		return i.get_data_for_import_preview()

	def start_import(self):
		from frappe.core.page.background_jobs.background_jobs import get_info
		from frappe.utils.scheduler import is_scheduler_inactive

		if is_scheduler_inactive() and not frappe.flags.in_test:
			frappe.throw(
				_("Scheduler is inactive. Cannot import data."), title=_("Scheduler Inactive")
			)

		enqueued_jobs = [d.get("job_name") for d in get_info()]

		if self.name not in enqueued_jobs:
			enqueue(
				start_import,
				queue="default",
				timeout=6000,
				event="data_import",
				job_name=self.name,
				data_import=self.name,
				now=frappe.conf.developer_mode or frappe.flags.in_test,
			)
			return True

		return False

	def export_errored_rows(self):
		return self.get_importer().export_errored_rows()

	def get_importer(self):
		return Importer(self.reference_doctype, data_import=self)


	@frappe.whitelist()
	def get_linked_org(self, throw_if_missing=False):
			# if not frappe.db.exists("Sales Partner", self.distributor):
			# 		if throw_if_missing:
			# 				frappe.throw('Sales Partner not found')

			# return [org.code for org in frappe.get_doc("Sales Partner", self.distributor).organization]
			return frappe.get_doc('MP', self.dm).get(self.distributor.lower() + '_org_code')



def has_permission(doc, ptype="read", user=None):
	user = user or frappe.session.user
	full_name = get_user_fullname(frappe.session['user'])
	if doc.approver_1_name == full_name or doc.approver_2_name == full_name or doc.dm_name == full_name:
		return True
	else:
		return False


def get_mop_query(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql(""" select mode_of_payment from `tabPayment Order Reference`
		where parent = %(parent)s and mode_of_payment like %(txt)s
		limit %(start)s, %(page_len)s""", {
			'parent': filters.get("parent"),
			'start': start,
			'page_len': page_len,
			'txt': "%%%s%%" % txt
		})

def get_supplier_query(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql(""" select supplier from `tabPayment Order Reference`
		where parent = %(parent)s and supplier like %(txt)s and
		(payment_reference is null or payment_reference='')
		limit %(start)s, %(page_len)s""", {
			'parent': filters.get("parent"),
			'start': start,
			'page_len': page_len,
			'txt': "%%%s%%" % txt
		})


###############################
@frappe.whitelist()
def get_preview_from_template(data_import, import_file=None, google_sheets_url=None):
	return frappe.get_doc("Data Import", data_import).get_preview_from_template(
		import_file, google_sheets_url
	)


@frappe.whitelist()
def form_start_import(data_import):
	return frappe.get_doc("Data Import", data_import).start_import()


def start_import(data_import):
	"""This method runs in background job"""
	data_import = frappe.get_doc("Data Import", data_import)
	try:
		i = Importer(data_import.reference_doctype, data_import=data_import)
		i.import_data()
	except Exception:
		frappe.db.rollback()
		data_import.db_set("status", "Error")
		frappe.log_error(title=data_import.name)
	finally:
		frappe.flags.in_import = False

	frappe.publish_realtime("data_import_refresh", {"data_import": data_import.name})


@frappe.whitelist()
def download_template(
	doctype="LPD", export_fields=None, export_records=None, export_filters=None, export_protect_area=None, file_type="Excel"
):
	"""
	Download template from Exporter
		:param doctype: Document Type
		:param export_fields=None: Fields to export as dict {'Sales Invoice': ['name', 'customer'], 'Sales Invoice Item': ['item_code']}
		:param export_records=None: One of 'all', 'by_filter', 'blank_template'
		:param export_filters: Filter dict
		:param file_type: File type to export into
	"""

	export_fields = frappe.parse_json(export_fields)
	export_filters = frappe.parse_json(export_filters)
	export_data = export_records != "blank_template"
	export_protect_area = frappe.parse_json(export_protect_area)

	e = Exporter(
		doctype,
		export_fields=export_fields,
		export_data=export_data,
		export_filters=export_filters,
		file_type=file_type,
		export_protect_area=export_protect_area,
		export_page_length=5 if export_records == "5_records" else None,
	)

	e.build_response()

@frappe.whitelist()
def download_list(
	doctype="LPD", export_fields=None, export_records=None, names=None, export_protect_area=None, file_type="Excel"
):
	"""
	Download template from Exporter
		:param doctype: Document Type
		:param export_fields=None: Fields to export as dict {'Sales Invoice': ['name', 'customer'], 'Sales Invoice Item': ['item_code']}
		:param export_records=None: One of 'all', 'by_filter', 'blank_template'
		:param export_filters: Filter dict
		:param file_type: File type to export into
	"""

	export_fields = frappe.parse_json(export_fields)
	export_filters = {"name": ["in", names]}
	export_data = export_records != "blank_template"
	export_protect_area = frappe.parse_json(export_protect_area)

	e = Exporter(
		doctype,
		export_fields=export_fields,
		export_data=export_data,
		export_filters=export_filters,
		file_type=file_type,
		export_protect_area=export_protect_area,
		export_page_length=5 if export_records == "5_records" else None,
	)

	e.build_response()


@frappe.whitelist()
def download_errored_template(data_import_name):
	data_import = frappe.get_doc("Data Import", data_import_name)
	data_import.export_errored_rows()


def import_file(
	doctype, file_path, import_type, submit_after_import=False, console=False
):
	"""
	Import documents in from CSV or XLSX using data import.

	:param doctype: DocType to import
	:param file_path: Path to .csv, .xls, or .xlsx file to import
	:param import_type: One of "Insert" or "Update"
	:param submit_after_import: Whether to submit documents after import
	:param console: Set to true if this is to be used from command line. Will print errors or progress to stdout.
	"""

	data_import = frappe.new_doc("Data Import")
	data_import.submit_after_import = submit_after_import
	data_import.import_type = (
		"Insert New Records" if import_type.lower() == "insert" else "Update Existing Records"
	)

	i = Importer(
		doctype=doctype, file_path=file_path, data_import=data_import, console=console
	)
	i.import_data()


##############


def import_doc(
	path,
	overwrite=False,
	ignore_links=False,
	ignore_insert=False,
	insert=False,
	submit=False,
	pre_process=None,
):
	if os.path.isdir(path):
		files = [os.path.join(path, f) for f in os.listdir(path)]
	else:
		files = [path]

	for f in files:
		if f.endswith(".json"):
			frappe.flags.mute_emails = True
			frappe.modules.import_file.import_file_by_path(
				f, data_import=True, force=True, pre_process=pre_process, reset_permissions=True
			)
			frappe.flags.mute_emails = False
			frappe.db.commit()
		elif f.endswith(".csv"):
			import_file_by_path(
				f,
				ignore_links=ignore_links,
				overwrite=overwrite,
				submit=submit,
				pre_process=pre_process,
			)
			frappe.db.commit()


def import_file_by_path(
	path,
	ignore_links=False,
	overwrite=False,
	submit=False,
	pre_process=None,
	no_email=True,
):
	if path.endswith(".csv"):
		print()
		print("This method is deprecated.")
		print('Import CSV files using the command "bench --site sitename data-import"')
		print("Or use the method frappe.core.doctype.data_import.data_import.import_file")
		print()
		raise Exception("Method deprecated")


def export_json(
	doctype, path, filters=None, or_filters=None, name=None, order_by="creation asc"
):
	def post_process(out):
		del_keys = ("modified_by", "creation", "owner", "idx")
		for doc in out:
			for key in del_keys:
				if key in doc:
					del doc[key]
			for k, v in doc.items():
				if isinstance(v, list):
					for child in v:
						for key in del_keys + ("docstatus", "doctype", "modified", "name"):
							if key in child:
								del child[key]

	out = []
	if name:
		out.append(frappe.get_doc(doctype, name).as_dict())
	elif frappe.db.get_value("DocType", doctype, "issingle"):
		out.append(frappe.get_doc(doctype).as_dict())
	else:
		for doc in frappe.get_all(
			doctype,
			fields=["name"],
			filters=filters,
			or_filters=or_filters,
			limit_page_length=0,
			order_by=order_by,
		):
			out.append(frappe.get_doc(doctype, doc.name).as_dict())
	post_process(out)

	dirname = os.path.dirname(path)
	if not os.path.exists(dirname):
		path = os.path.join("..", path)

	with open(path, "w") as outfile:
		outfile.write(frappe.as_json(out))


def export_csv(doctype, path):
	from frappe.core.doctype.data_export.exporter import export_data

	with open(path, "wb") as csvfile:
		export_data(doctype=doctype, all_doctypes=True, template=True, with_data=True)
		csvfile.write(frappe.response.result.encode("utf-8"))






