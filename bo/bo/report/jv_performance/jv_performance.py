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
		{"label": "Dx", "fieldname": "dx_p", "fieldtype": "Percent", "width": 70},
		{"label": "DPPU", "fieldname": "dp_p", "fieldtype": "Percent", "width": 70},
		{"label": "Number", "fieldname": "nr_p", "fieldtype": "Percent", "width": 70},
	]
	return columns


def get_items(filters):
	conditions = []
	if filters.get("start_date") and filters.get("end_date"):
		conditions.append("date between {} and {}".format(frappe.db.escape(filters.get('start_date')), frappe.db.escape(filters.get('end_date'))))

	items = []
	if conditions:
		items = frappe.db.sql("""with dppu as( SELECT * from tabDPPU where workflow_state IN ('DM Recap', 'JV', 'JV Closed', 'JV has Issue') AND jv_date IS not NULL AND cash_transfer IN ('Cash', 'Transfer') {}),
			dp as (SELECT mss, COUNT(*) as cnt, SUM(number) as nr, COUNT(DISTINCT dx_user) as dxtotal from dppu GROUP BY mss),
			dpx as (SELECT COUNT(DISTINCT dx_user) as cnt, mss as mssx FROM dppu WHERE workflow_state IN ('JV Closed', 'JV has Issue') GROUP BY mss),
			dpp as (SELECT COUNT(*) as cnt, mss as mssp FROM dppu WHERE workflow_state IN ('JV Closed', 'JV has Issue') GROUP BY mss),
			dnr as (SELECT SUM(number) as nr, mss as mssr FROM dppu WHERE workflow_state IN ('JV Closed', 'JV has Issue') GROUP BY mss)
			SELECT dp.mss, ROUND(dpx.cnt*100/dp.dxtotal, 2) AS dx_p,
			ROUND(dpp.cnt*100/dp.cnt, 2) AS dp_p,
			ROUND(dnr.nr*100/dp.nr, 2) AS nr_p
				from dp, dpx, dpp, dnr WHERE dpx.mssx = dpp.mssp AND dpp.mssp = dp.mss AND dnr.mssr = dp.mss"""
						.format("and "+" and ".join(conditions)), filters)
	return items