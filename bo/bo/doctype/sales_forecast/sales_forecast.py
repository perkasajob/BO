# -*- coding: utf-8 -*-
# Copyright (c) 2022, Perkasa JoB and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class SalesForecast(Document):
	def validate(self):
		user = frappe.session.user
		if "MKT" in frappe.get_roles(user) :
			self.mkt = user
		if "PM" in frappe.get_roles(user):
			self.pm = user
		if "PPIC" in frappe.get_roles(user):
			self.ppic = user

