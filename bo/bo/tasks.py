from __future__ import unicode_literals
from frappe import _
import frappe
from frappe.utils.background_jobs import enqueue

def daily():	
	# frappe.log_error(message="I Am on the background" , title="test background")
	set_DPPU_overdue(14) # 10 days

def set_DPPU_overdue(period):
	from frappe.desk.doctype.event.event import get_events
	from frappe.utils import nowdate
	# check for overdue
	# today = nowdate()
	frappe.db.sql("""update `tabDPPU` set workflow_state = 'Overdue Refund' where DATEDIFF(NOW(),date)>{} and workflow_state = 'Refund'""".format(period))
	frappe.db.commit()