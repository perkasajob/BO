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
from frappe.utils import today


class DxAcc(Document):
	def validate(self):
		pass

	def parseXLS(self):
		file_url = self.get_full_path() # file attachment only the first one attached
		fname = os.path.basename(file_url)
		fxlsx = re.search("^{}.*\.xlsx".format("Dx"), fname)

		if(fxlsx): # match
			with open( file_url , "rb") as upfile:
				fcontent = upfile.read()
			if frappe.safe_encode(fname).lower().endswith("xlsx".encode('utf-8')):
				from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file
				rows = read_xlsx_file_from_attached_file(fcontent=fcontent)
			columns = rows[0]
			rows.pop(0)
			data = rows
			res = check_dx_list(self.name, rows)
			if res:
				columns[0] = '<span style="color:red">Error ID Not Found</span>'
				return {"columns": columns, "data": res, "filename": self.filename}
			frappe.enqueue(import_loan, name=self.name, rows=rows, now=True if len(rows) < 200 else False)
			return {"columns": columns, "data": data, "filename": self.filename}
		else:
			return {"status" : "Error", "filename": fname}


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

def check_dx_list(name, rows):
	res = []
	for row in rows:
		if not frappe.db.exists("Dx", row[0]):
			res.append(row)
	return res

def import_loan(name, rows):
	for row in rows:
		dx = frappe.get_doc("Dx", row[0])
		line = row[4] # line
		if(row[1]): # Acc number
			dx_book = 'loan_' + line
			dx.append(dx_book, {'number': row[1], 'ref_nr': row[2], 'note': row[3] + ' -' + name, 'line': line, 'type': 'DxAcc', 'date': today()})
		dx.save()
	frappe.publish_realtime('Dx acc', 'Success ...')