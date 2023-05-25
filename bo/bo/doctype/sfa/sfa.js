// Copyright (c) 2022, Sistem Koperasi and contributors
// For license information, please see license.txt

frappe.ui.form.on('SFA', {
	target_date: function(frm){
		// var datestr = frappe.datetime.str_to_obj(frm.doc.target_date).getMonth()
		frm.set_value("date_code", moment(frm.doc.target_date).format("YYMM"))
	},
	onload: function(frm){
		if(frappe.user.has_role("DM") && frappe.user.name != "Administrator" && !frm.doc.dm){
			frm.set_value("dm", "DM-" + frappe.session.user.replace(/@.*/g,"").toUpperCase())
		}
	}
});
