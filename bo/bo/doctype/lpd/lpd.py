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
from frappe.utils.background_jobs import enqueue
from frappe.utils.csvutils import validate_google_sheets_url
from frappe import _
import pprint
import re


class LPD(Document):
	def validate(self):
		pass

	def parseXLS(self):
		file_doc = frappe.get_doc("File", {"file_url": self.file})
		file_content = file_doc.get_content()
		data = []
		# return file_content

		from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file
		rows = read_xlsx_file_from_attached_file(fcontent=file_content)
		dxname = frappe.db.sql('''SELECT name FROM tabDx
								WHERE name LIKE "%%%s"''' % '" OR name LIKE "%'.join(rows[6][8:18]), as_list=True)
		dx = self.match_and_replace(rows[6][8:18], dxname)

		_rows = [r for r in  [r for r in rows[8:] if r] if r[1]] # cleaning empties

		if _rows:
			item_hjms = frappe.db.get_all(
					'Item',
					filters={'name': ['in', [str(r[1]) for r in _rows]]},
					fields=['name', 'hjm_1','hjm_2','hjm_3']
			)

			# Create a dictionary for quick hjm lookup
			hjm_dict = {item['name']: [item['hjm_1'], item['hjm_2'], item['hjm_3']] for item in item_hjms}
			data = [d + hjm_dict[str(d[1])] for d in _rows if str(d[1]) in hjm_dict.keys()]

		return {"year": rows[1][9], "month": rows[1][11], "tp": rows[1][15],
					"outid": rows[3][9], "dx": dx,
					"columns": rows[7], "data": data, "dxname": dxname}


	def match_and_replace(self, var1, var2):
		result = []
		for item in var1:
				# Find the match where item is the suffix
				match = next((x[0] for x in var2 if x[0].endswith('-' + item)), None)
				if match:
						result.append(match)  # If match found, append it to result
				else:
						result.append(item)   # Otherwise, keep the original item

		return result

	def dump_variable_to_file(variable_content, filename="output.json"):
		# You can use frappe.get_site_path to save it in the site folder
		file_path = "output.json"

		if isinstance(variable_content, bytes):
			variable_content = variable_content.decode("utf-8")

    # Open the file in write mode and dump the content
		with open(file_path, "w") as file:
				# file.write(str(variable_content))  # Convert to string if not already
				pprint.pprint(variable_content, stream=file)




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

