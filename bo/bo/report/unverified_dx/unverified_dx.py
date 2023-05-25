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
		{"label": "Dx", "fieldname": "dx", "fieldtype": "Link", "options": "Dx", "width": 400},
		{"label": "DM", "fieldname": "dm", "fieldtype": "Link", "options": "MP", "width": 150},
		{"label": "MSS", "fieldname": "mss", "width": 150}
	]
	return columns


def get_items(filters):
	conditions = []
	if filters.get("year"):
		conditions.append("YEAR(dp.date)=%(year)s")

	items = []
	if conditions:
		items = frappe.db.sql("""SELECT dx.name as dx, mp.full_name as dm, mp.mss as mss FROM tabDx dx left join tabMP mp on dx.mp = mp.name WHERE dx.is_verified=0 AND dx.territory <> 'Tidak Aktif'"""
						.format("and "+" and ".join(conditions)), filters)
	# (SELECT * FROM tabDx dx WHERE NOT EXISTS (SELECT * from tabDPPU dp WHERE dp.dx_user = dx.name AND dp.workflow_state IN ("JV Closed") {}))
	return items
