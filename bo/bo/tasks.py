from __future__ import unicode_literals
from frappe import _
import frappe
from frappe.utils.background_jobs import enqueue
from frappe.utils import nowdate

def daily():	
	set_DPPU_overdue(14) # 14 days
	move_dx_adv_to_acc()

def set_DPPU_overdue(period):
	from frappe.desk.doctype.event.event import get_events
	frappe.db.sql("""update `tabDPPU` set workflow_state = 'Overdue Refund' where DATEDIFF(NOW(),date)>{} and (workflow_state = 'Refund' or workflow_state = 'DM Received')""".format(period))
	frappe.db.commit()


@frappe.whitelist()
def move_dx_adv_to_acc(today=nowdate()):
	# today = nowdate()
	for i in range(2):		
		adv_idx = str(i) if i > 0 else ''
		advs = frappe.get_list('SP', filters=[['parentfield','=','adv'+ adv_idx],['date','=',today], ['type','in',['AC','AT']]], fields=['*'])

		for adv in advs:
			suffix = adv.line if int(adv.line) > 1 else '' 
			idx = frappe.db.count('SP', {'parent': adv.parent, 'parentfield': 'loan' + suffix })
			adv = frappe.get_doc("SP", adv.name)
			adv.parentfield = 'loan' + suffix
			adv.idx = idx + 1
			adv.save()
			dx =  frappe.get_doc("Dx", adv.parent)
			dx.save()
			frappe.db.commit()
	return {"status" : "success"}