# -*- coding: utf-8 -*-
# Copyright (c) 2020, Sistem Koperasi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import today, flt

class AdvInstall(Document):
	def on_submit(self):
		dppu = frappe.get_doc('DPPU', self.dppu)
		line = dppu.mr_user[-1]
		ct = 'AC' if dppu.cash_transfer == 'Cash' else 'AT'
		# ls = line if int(line) > 1 else '' # Line Suffix
		sp = frappe.db.sql("select * from `tabSP` where dppu='{}' and number > 0".format(self.dppu), as_dict=1)
		if len(sp) > 0:
			frappe.msgprint("already booked on "+ str(sp.date) + ", Adv Install: ")
		else:
			dx = frappe.get_doc('Dx', dppu.dx_user)
			note = "Adv-Inst by {}, {} {}".format(frappe.session.user, self.blanko_nr, self.note)
			dx.append('loan'+line,{'date':today(),'number': self.number, 'dppu': dppu.name, 'type':ct, 'line': int(line), 'note': note, 'ref_nr': self.ref_nr})
			# dx.append('mkt'+ls ,{'date':today(),'number': self.number, 'dppu': dppu.name, 'type':ct, 'line': line, 'note': note, 'territory': dx.territory, 'ref_nr': self.ref_nr})
			dx.save()
			frappe.db.commit()
