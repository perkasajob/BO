// Copyright (c) 2020, Sistem Koperasi and contributors
// For license information, please see license.txt

frappe.ui.form.on('DKH', {
	onload: function(frm) {
		// frm.set_value('month_code',frm.doc.start_on.substr(2,5).replace('-',''))
		set_filter(frm)
		frm.set_value('date_code', moment(cur_frm.doc.date).format("DDMMYY"))
	},
	date: function(frm) {
		// frm.set_value('date_code', frm.doc.date.substr(2,9).replaceAll('-',''))
		frm.set_value('date_code', moment(cur_frm.doc.date).format("DDMMYY"))
	}
});
function set_filter(frm){
    if(frappe.user.has_role("SE") && frappe.user.name != "Administrator"){
          frm.set_value("sales_exec", frappe.session.user.replace(/@.*/g,""))
	}
}

