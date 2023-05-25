# -*- coding: utf-8 -*-
# Copyright (c) 2022, Sistem Koperasi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class SFA(Document):
	def validate(self):
		user = frappe.session.user
		if "DM" in frappe.get_roles(user) :
			self.mkt = user

