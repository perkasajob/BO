// Copyright (c) 2020, Sistem Koperasi and contributors
// For license information, please see license.txt

frappe.ui.form.on('DKH', {
	onload: function(frm) {
		set_filter(frm)
		frm.set_value('date_code', moment(cur_frm.doc.date).format("YYMMDD"))
	},
	date: function(frm) {
		// frm.set_value('date_code', frm.doc.date.substr(2,9).replaceAll('-',''))
		frm.set_value('date_code', moment(cur_frm.doc.date).format("YYMMDD"))
	},
	territory: function(frm) {
		set_filter_by_territory(frm)
	}
});

function set_filter(frm){
    if(frappe.user.has_role("SE") && frappe.user.name != "Administrator"){
          frm.set_value("sales_exec", frappe.session.user.replace(/@.*/g,""))
	}
}

function set_filter_by_territory(frm){
	frappe.call('bo.bo.getTerritory', {
		territory: frm.doc.territory
	}).then(r => {
		frm.set_query("outlet", "visits", function(doc, cdt, cdn) {
			return{
				filters: {
					'territory': ['in', r.message.map((o)=>{return o.name})]
				}
			}
		});
	})
}

