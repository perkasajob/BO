
import frappe, re
from frappe.utils.user import get_user_fullname

def dppu_has_permission(doc):
	u = frappe.db.sql("""select * from `tabDPPU` dppu left join `tabDM` dm ON dppu.dm_user = dm.name where sm_user='{}'""".format(frappe.session.user),as_dict=True)
	if "SM" in frappe.get_roles(frappe.session.user):
		return True
	else:
		return False

def dppu_get_permission_query_conditions(user):
	if not user: user = frappe.session.user

	if user == "Administrator":
		return

	full_name = get_user_fullname(user)
	mps = frappe.db.get_list('MP', filters={'user_id':user}, fields=('name'))

	fields = frappe.get_meta("DPPU").get("fields", {
		"fieldtype":"Link",
		"options": ("MP")
	})
	for mp in mps:
		return  ' or '.join(["`tabDPPU`.{}='{}'".format(f.fieldname, mp.name) for f in fields] + ["`tabDPPU`.{}_name='{}'".format(f.fieldname, full_name) for f in fields])

def dkh_get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	if user == "Administrator":
		return
	if "SC" in frappe.get_roles(user):
		return """(`tabDKH`.parent_sales_executive = '{}')""".format(re.sub("@.*", "", user))

def dpl_get_permission_query_conditions(user):
	if not user: user = frappe.session.user

	if user == "Administrator":
		return

	full_name = get_user_fullname(user)
	mps = frappe.db.get_list('MP', filters={'user_id':user}, fields=('name'))

	fields = frappe.get_meta("DPL").get("fields", {
		"fieldtype":"Link",
		"options": ("MP")
	})
	for mp in mps:
		return  ' or '.join(["`tabDPL`.{}='{}'".format(f.fieldname, mp.name) for f in fields] + ["`tabDPL`.{}_name='{}'".format(f.fieldname, full_name) for f in fields])