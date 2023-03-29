// Copyright (c) 2020, Sistem Koperasi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dx', {
	onload: function(frm) {
		if(!frappe.user.has_role(['Administrator', 'System Manager', 'Report Manager', 'CSD', 'ARCO', 'Accounts Manager', 'MSS']))
			$('.form-attachments').remove()
	}
});

frappe.ui.form.on('SP', {
	number: function(frm, cdt, cdn) {
		if(frappe.user.name != "Administrator" && !frappe.user.has_role('Accounts Manager')){
			var o = locals[cdt][cdn]
			if(frm.doc[o.parentfield][o.idx-1].number > 0){
				frm.doc[o.parentfield][o.idx-1].number *= -1
				frm.refresh_field(o.parentfield)
			}
		}
	}

})