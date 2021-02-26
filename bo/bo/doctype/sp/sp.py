# -*- coding: utf-8 -*-
# Copyright (c) 2020, Sistem Koperasi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document
from frappe import _, scrub, ValidationError
import frappe

class SP(Document):
	def validate(self):
		pass
		# frappe.msgprint(_("{0} {1} validated").format(self.saldo , self.name))

	def on_submit(self):
		pass
		# frappe.msgprint(_("{0} {1} submitted").format(self.saldo , self.name))
