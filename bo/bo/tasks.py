from __future__ import unicode_literals
from frappe import _
import frappe
from frappe.utils.background_jobs import enqueue

def daily():	
	set_DPPU_overdue(14) # 14 days

def set_DPPU_overdue(period):
	from frappe.desk.doctype.event.event import get_events
	from frappe.utils import nowdate
	# today = nowdate()
	frappe.db.sql("""update `tabDPPU` set workflow_state = 'Overdue Refund' where DATEDIFF(NOW(),date)>{} and (workflow_state = 'Refund' or workflow_state = 'DM Received')""".format(period))
	frappe.db.commit()