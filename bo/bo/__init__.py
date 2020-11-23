# -*- coding: utf-8 -*-
# Copyright (c) 2020, Sistem Koperasi

import frappe
from frappe.utils import today, flt


@frappe.whitelist()
def dkh_get_permission_query_conditions(user=None):
	if not user: user = frappe.session.user
	return """(`tabDKH`.parent_sales_executive = '{}')""".format(user)
	if user == "Administrator":
		return
	if "SC" in frappe.get_roles(user):
		return """(`tabDKH`.parent_sales_executive = '{}')""".format(user)

@frappe.whitelist()
def getTerritory(territory):
	return get_child_nodes("Territory", territory)

def get_child_nodes(group_type, root):
	lft, rgt = frappe.db.get_value(group_type, root, ["lft", "rgt"])
	return frappe.db.sql(""" Select name, lft, rgt from `tab{tab}` where
			lft >= {lft} and rgt <= {rgt} order by lft""".format(tab=group_type, lft=lft, rgt=rgt), as_dict=1)