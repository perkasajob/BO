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
from bo.bo.utils.exporter import Exporter
from frappe.utils.background_jobs import enqueue
from frappe.utils.csvutils import validate_google_sheets_url
from frappe import _
import re
import pandas as pd
import numpy as np
from collections import defaultdict

class SLS(Document):
	def validate(self):
		pass

	def parseXLS(self):
		file_doc = frappe.get_doc("File", {"file_url": self.file})
		file_content = file_doc.get_content()

		from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file
		rows = read_xlsx_file_from_attached_file(fcontent=file_content)

		df = pd.DataFrame(rows[1:], columns=rows[0])

		lst = df.groupby(['TPID', 'outid', 'proid']).agg({
    			'quantity': 'sum', 'value_net': 'sum', 'disc_p': 'max'})

		cascaded_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

		for (outer_key1, outer_key2, outer_key3), inner_dict in lst.to_dict(orient='index').items():
			self.append("items", {
				'tpid': outer_key1,
				'outid': outer_key2,
				'proid': outer_key3,
				'qty' : inner_dict['quantity'],
				'disc' : inner_dict['disc_p']*100,
				'value_net': inner_dict['value_net'],
			})
			cascaded_dict[outer_key1][outer_key2][outer_key3] = {
					'qty': inner_dict['quantity'],
					'disc' : inner_dict['disc_p']*100,
					'value_net': inner_dict['value_net']
			}
		# self.save()
		# TODO: PJOB don't forget to activate save above & check the sql syntax
		# NOTE:
		# - dpl_sls = ON from Sales
		# - qty_sls = Quantity sold in Sales
		# - tnof_sls = Total Nominal Off Sales
		# - .dpl = LPD ON sales
		# - .tpdisc = LPD Total (On + Off) Discount in %
		# - .tnof = LPD Total Nominal Off

		sql	= '''
				UPDATE tabLPD
				JOIN `tabLPD Item` ON `tabLPD Item`.parent = tabLPD.name
				JOIN (
						SELECT
								tabSLS.name AS SLS_name,
								tabSLS.year,
								tabSLS.month,
								`tabSLS Item`.*
						FROM tabSLS
						JOIN `tabSLS Item` ON `tabSLS Item`.parent = tabSLS.name
				) AS SLS ON SLS.month = tabLPD.month
								AND SLS.year = tabLPD.year
								AND SLS.outid = tabLPD.outid
								AND SLS.proid = CONVERT(`tabLPD Item`.item_code, CHAR)
				SET `tabLPD Item`.dpl_sls = SLS.disc,
						`tabLPD Item`.qty_sls = SLS.qty,
						`tabLPD Item`.tnof_sls =
											CASE
												WHEN SLS.disc >= `tabLPD Item`.tpdisc  THEN 0
												WHEN `tabLPD Item`.dpl > SLS.disc THEN `tabLPD Item`.tnof
												ELSE (`tabLPD Item`.tpdisc - SLS.disc)/100 * `tabLPD Item`.hna
											END,
						`tabLPD Item`.dpl_dt =`tabLPD Item`.dpl - SLS.disc,
						`tabLPD Item`.debug =
											CASE
												WHEN SLS.disc >= `tabLPD Item`.tpdisc THEN CONCAT( CAST(SLS.disc as CHAR), " >= ", CAST(`tabLPD Item`.tpdisc as CHAR))
												WHEN `tabLPD Item`.dpl > SLS.disc THEN CONCAT( CAST(`tabLPD Item`.dpl as CHAR), " > ", CAST(SLS.disc as CHAR))
												ELSE "ELSE"
											END

				WHERE tabLPD.month = "{0}" AND tabLPD.year = {1};'''.format(self.month, self.year)
		frappe.db.sql(sql)
		frappe.db.commit()

		return cascaded_dict

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
	doctype="SalesSingle Single", export_fields=None, export_records=None, export_filters=None, export_protect_area=None, file_type="Excel"
):
	"""
	Download template from Exporter
		:param doctype: Document Type
		:param export_fields=None: Fields to export as dict {'SalesSingle Single Invoice': ['name', 'customer'], 'SalesSingle Single Invoice Item': ['item_code']}
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
	doctype="SalesSingle Single", export_fields=None, export_records=None, names=None, export_protect_area=None, file_type="Excel"
):
	"""
	Download template from Exporter
		:param doctype: Document Type
		:param export_fields=None: Fields to export as dict {'SalesSingle Single Invoice': ['name', 'customer'], 'SalesSingle Single Invoice Item': ['item_code']}
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
