# -*- coding: utf-8 -*-
# Copyright (c) 2020, Quantum Labs and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document
from frappe import _, scrub, ValidationError
import frappe

class SP(Document):
	def validate(self):
		frappe.msgprint(("SP validated"))
		# frappe.msgprint(_("{0} {1} validated").format(self.saldo , self.name))

	def on_submit(self):
		frappe.msgprint(("SP submitted"))
		# frappe.msgprint(_("{0} {1} submitted").format(self.saldo , self.name))
