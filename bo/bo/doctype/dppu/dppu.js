// Copyright (c) 2020, Quantum Labs and contributors
// For license information, please see license.txt

frappe.ui.form.on('DPPU', {
    onload: function(frm){
        set_filter(frm)
    },
    refresh: function(frm){
        set_norek_btn(frm)
    },
    validate: function(frm){
        if (frm.doc.date < get_today()) {
            frappe.msgprint(__("You can not select past date in From Date"));
            frappe.validated = false;
        }
    }
})

function set_norek_btn(frm){
    if(frappe.user.has_role("MSD")){
        frm.add_custom_button(__('Get Dx Rex'), function(){
            frappe.db.get_value("Dx", {"name": frm.doc.dx_user},["no_rek","nama_rek", "bank", "saldo","is_id"], function(v) {           
                frappe.msgprint('<table><tr><td>Nama :&nbsp</td><td>'+v.nama_rek +'</td></tr><table><tr><td>NRek :&nbsp</td><td>'+ v.no_rek +'</td></tr><table><tr><td>Saldo :&nbsp</td><td>' + v.saldo +'</td></tr><table><tr><td>IS id   :&nbsp</td><td>'+ v.is_id +'</td><td>');
                
            });
        });
        frm.add_custom_button(__('Go Dx'), function(){
            frappe.set_route("Form", "Dx", frm.doc.dx_user)
        });
    }
}

function set_filter(frm){
    if(frappe.user.has_role("DM") && frappe.user.name != "Administrator"){
          frm.set_value("dm_user", "DM-" + frappe.session.user.replace(/@.*/g,"").toUpperCase())
          frappe.db.get_value("DM",frm.doc.dm_user,"territory",function(res){
              if(res != undefined){
                frm.set_value("territory", res.territory)
              }else {
                //frappe.msgprint("You may not have a DM role, not allowed !")
              } 
          })
    }      
    if(frm.doc.dm_user){
        console.log("I am called !!!!")
		frm.set_query("mr_user", function(doc) {
			return {
				filters: {
					'dm_id': doc.dm_user
				}
			};
		});
		frm.set_query("dx_user", function(doc) {
            return {
                "filters": {
                    "territory": doc.territory
                }
            };
        });
    }
}
