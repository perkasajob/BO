// Copyright (c) 2020, Sistem Koperasi and contributors
// For license information, please see license.txt

frappe.ui.form.on('DKH', {
	start_on: function(frm) {
		frm.set_value('month_code',frm.doc.start_on.substr(2,5).replace('-',''))
	}
});
