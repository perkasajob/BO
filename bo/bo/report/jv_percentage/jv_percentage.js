// Copyright (c) 2016, Sistem Koperasi and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["JV Percentage"] = {
	"filters": [
		{
			"fieldname": "mss",
			"label": "MSS",
			"fieldtype": "Link",
			"options": "MSS",
			"width": "120"
		},
		{
			"fieldname": "workflow_state",
			"label": "Status",
			"fieldtype": "Link",
			"options": "Workflow State",
			"width": "100"
		},
		{
			"fieldname":"year",
			"label": __("Year"),
			"fieldtype": "Data",
			"width": "70",
			"default": frappe.datetime.get_today().slice(0,4),
		},
	],

	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname == "dx_user" && data) {
			value = `<a href='/desk#List/DPPU/List?dx_user=${value}'>` + value + "</a>";
		}

		return value;
	}
};
