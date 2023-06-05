// Copyright (c) 2016, Sistem Koperasi and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["JV Performance"] = {
	"filters": [
		{
			'fieldname': 'start_date',
			'fieldtype': 'Date',
			'label': 'Start Date',
			'reqd': 1,
			'default': frappe.datetime.add_months(frappe.datetime.nowdate(), -3)
		},{
			'fieldname': 'end_date',
			'fieldtype': 'Date',
			'label': 'End Date',
			'reqd': 1,
			'default': frappe.datetime.nowdate()
		}
	],

	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname == "mss" && data) {
			value = `<a href='/desk#List/DPPU/List?mss=${value}&workflow_state=JV'>` + value + "</a>";
		}

		return value;
	}
};
