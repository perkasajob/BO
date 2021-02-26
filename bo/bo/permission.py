
import frappe, re

def dppu_get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	if user == "Administrator":
		return
	if "SM" in frappe.get_roles(user):
		# u = frappe.db.sql("""select * from `tabDPPU` dppu left join `tabDM` dm ON dppu.dm_user = dm.name where sm_user='{}'""".format(frappe.session.user),as_dict=True)
		# return frappe.db.sql("""select * from `tabDPPU` dppu left join `tabDM` dm ON dppu.dm_user = dm.name where sm_user='{}'""".format(frappe.session.user))
		# return """(select * from `tabDPPU` dppu left join `tabDM` dm ON dppu.dm_user = dm.name where sm_user='{}')""".format(user)
		return """(`tabDPPU`.sm_user = '{}')""".format(user)


def dppu_has_permission(doc):
	u = frappe.db.sql("""select * from `tabDPPU` dppu left join `tabDM` dm ON dppu.dm_user = dm.name where sm_user='{}'""".format(frappe.session.user),as_dict=True)
	if "SM" in frappe.get_roles(frappe.session.user):
		return True
	else:
		return False

def dkh_get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	if user == "Administrator":
		return
	if "SC" in frappe.get_roles(user):
		return """(`tabDKH`.parent_sales_executive = '{}')""".format(re.sub("@.*", "", user))