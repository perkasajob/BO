// Copyright (c) 2016, Sistem Koperasi and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Unverified Dx"] = {
	"filters": [
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
