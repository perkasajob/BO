from __future__ import unicode_literals
from frappe import _
import frappe
from frappe.utils.background_jobs import enqueue
from frappe.utils import nowdate
from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification,\
	get_title, get_title_html
from datetime import datetime	

def daily():	
	set_DPPU_overdue(14) # 14 days
	expire_dx_adv()

def set_DPPU_overdue(period):
	from frappe.desk.doctype.event.event import get_events
	frappe.db.sql("""update `tabDPPU` set workflow_state = 'Overdue Refund', amount_refund = number where DATEDIFF(NOW(),date)>{} and (workflow_state = 'Refund' or workflow_state = 'DM Received')""".format(period))
	frappe.db.commit()


@frappe.whitelist()
def expire_dx_adv(today=nowdate()):
	for i in range(2):		
		adv_idx = str(i) if i > 0 else ''
		# advs = frappe.get_list('Adv Item', filters=[['parentfield','=','adv'+ adv_idx],['date','<=',today], ['type','in',['AC','AT']]], fields=['*'])
		advs = frappe.get_list('Adv Item', filters=[['parentfield','=','adv'+ adv_idx], ['date','<=',today]], fields=['*'])

		for adv in advs:
			suffix = adv.line if int(adv.line) > 1 else '' 
			# idx = frappe.db.count('SP', {'parent': adv.parent, 'parentfield': 'loan' + suffix })
			# adv = frappe.get_doc("Adv Item", adv.name)
			dx = frappe.get_doc(adv.parenttype, adv.parent)
			dx.append('mkt'+suffix ,{'date':adv.date,'number': adv.number, 'dppu': adv.dppu, 'type':adv.type, 'line': adv.line, 'note': adv.note, 'territory': adv.territory})
			dx.validate()
			dx.save()
			mkt = frappe.get_doc({'doctype': 'Mkt','date':adv.date,'number': adv.number, 'dppu': adv.dppu, 'line': adv.line, 'note': adv.note, 'territory': adv.territory, 'dx': dx.name}).insert(ignore_permissions=True)
			mkt.submit()
			Event_doc, message = make_to_do(adv.parent, adv.owner)
			#frappe.delete_doc("SP", adv.name)
			notification_doc = {
				'type': 'To Do',
				'document_type': "",
				'document_name': Event_doc.name,
				'subject': message,
				'from_user': "Administrator",
				'email_content': '<div>{}</div>'.format(message)
			}

			enqueue_create_notification(adv.owner, notification_doc)
			
	frappe.db.commit()
	
	return {"status" : "success"}

def make_to_do(dx, user):
	message = "Dx {} Installment is overdue".format(dx)
	Event_doc=frappe.new_doc("ToDo")
	Event_doc.status="Open"
	Event_doc.priority="Medium"
	Event_doc.allocated_to=user
	Event_doc.date=nowdate()
	Event_doc.description=(message)
	Event_doc.flags.ignore_mandatory = True
	Event_doc.save()
	return Event_doc, message

		