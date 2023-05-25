# Copyright (c) 2013, Sistem Koperasi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns = get_columns(filters)
	data = get_items(filters)
	return columns, data



def get_columns(filters):
	"""return columns"""
	columns = [
		{"label": "MSS", "fieldname": "mss", "fieldtype": "Data", "width": 120},
		{"label": "Dx", "fieldname": "dx_user", "width": 350},
		{"label": "Status", "fieldname": "workflow_state", "width": 100},
		{"label": "Percent", "fieldname": "percent", "width": 70},
		{"label": "DPPU", "fieldname": "dppu", "width": 70},
		# {"label": "Visited", "fieldname": "visited", "fieldtype": "Check", "width": 50},
		{"label": "Year", "fieldname": "year", "width": 70}
	]
	return columns


def get_items(filters):
	conditions = []
	if filters.get("mss"):
		conditions.append("mss=%(mss)s")
	if filters.get("year"):
		conditions.append("YEAR(date)=%(year)s")
	if filters.get("workflow_state"):
		conditions.append("workflow_state=%(workflow_state)s")

	items = []
	if conditions:
		items = frappe.db.sql("""select mss, dx_user, workflow_state, ROUND(COUNT(*)*100/SUM(COUNT(*)) OVER(PARTITION BY YEAR(DATE),dx_user), 2) AS percent
					, Count(*) as dppu, YEAR(DATE) as year  from tabDPPU where workflow_state IN ('DM Received', 'DM Send Out', 'DM Recap', 'JV', 'Closed', 'JV has Issue') AND jv_date IS not NULL {} GROUP BY YEAR(date),mss,dx_user, workflow_state ORDER BY YEAR(date) DESC, mss"""
						.format("and "+" and ".join(conditions)), filters)
	return items
