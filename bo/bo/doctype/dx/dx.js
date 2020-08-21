// Copyright (c) 2020, Quantum Labs and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dx', {
	// refresh: function(frm) {

	// }
});

frappe.ui.form.on('SP', {
	number: function(frm, cdt, cdn) {
		if(frappe.user != "Administrator"){
		    var o = locals[cdt][cdn]
		    if(frm.doc[o.parentfield][o.idx-1].number > 0){
		        frm.doc[o.parentfield][o.idx-1].number *= -1
		        frm.refresh_field(o.parentfield)
		    }
		}
	}
})