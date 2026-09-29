# -*- coding: utf-8 -*-
# Copyright (c) 2020, Sistem Koperasi

import frappe
from frappe.utils import today, flt, cstr


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


@frappe.whitelist(allow_guest=True)
def enqueue_resave_dx():    
    frappe.enqueue(resave_dx, queue="default")
    return {"status": "Job enqueued"}

@frappe.whitelist(allow_guest=True)
def resave_dx():
    """Background job to re-save all records in the Dx DocType list."""
    frappe.set_user("Administrator")
    dx_records_dict = frappe.get_all("Dx", fields=["name"])
    dx_records = [d.name for d in dx_records_dict]
    
    for doc_name in dx_records:
        try:
            doc = frappe.get_doc("Dx", doc_name)
            doc.flags.ignore_permissions = True
            doc.save()            
        except Exception:
            frappe.db.rollback()
            frappe.log_error(title=f"Failed to resave {doc_name}")
    frappe.db.commit()