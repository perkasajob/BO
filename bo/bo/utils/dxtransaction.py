# -*- coding: utf-8 -*-
# Copyright (c) 2020, Sistem Koperasi

import frappe
from frappe.utils import today, flt


@frappe.whitelist()
def get_logged_user():
    return frappe.session.user


@frappe.whitelist()
def update_sp(dppu=None, number=None):
	if number == None or dppu == None:
		return {"status":" error "}

	dppu = frappe.get_doc('DPPU', dppu)	
	if int(number) > int(dppu.number):
		number = dppu.number

	ct = 'C' if dppu.cash_transfer == 'Cash' else 'T'
	dx = frappe.get_doc('Dx', dppu.dx_user)
	dx.append('dppu',{'date':today(),'number': int(number), 'dppu': dppu.name, 'type':ct})
	dx.save()
	frappe.db.commit()
	return dx
