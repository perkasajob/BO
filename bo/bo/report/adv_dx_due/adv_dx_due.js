frappe.query_reports["Adv Dx Due"] = {
	"filters": [
		{
			"fieldname":"start_date",
			"label": "Start Date",
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default": frappe.datetime.get_today(),
		},
		{
			"fieldname":"end_date",
			"label": "End Date",
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default": frappe.datetime.get_today(),
		}
	]
};