# -*- coding: utf-8 -*-
# Copyright (c) 2020, Sistem Koperasi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils.user import get_user_fullname

class DKH(Document):
	def onload(self):
		"""Load address and contacts in `__onload`"""
		full_name = get_user_fullname(frappe.session['user'])
		# self.set_onload('sales_order', 1000)
