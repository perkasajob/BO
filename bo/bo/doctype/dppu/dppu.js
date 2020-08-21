// Copyright (c) 2020, Quantum Labs and contributors
// For license information, please see license.txt

frappe.ui.form.on('DPPU', {
    onload: function(frm){
		set_filter(frm)
		set_color_saldo(frm)
    },
    refresh: function(frm){
		set_norek_btn(frm)
		set_color_saldo(frm)
		set_refund_btn(frm)
    },
    validate: function(frm){
        if (frm.doc.date < frappe.datetime.get_today()) {
            frappe.msgprint(__("You can not select past date in From Date"));
            frappe.validated = false;
        }
	},
	amount_refund: function(frm){
		if(frm.doc.amount_refund > frm.doc.number){
			frm.set_value('amount_refund', frm.doc.number)
			frappe.msgprint(__("Cannot input the amount greater than Number !"), "Error");
		}
		set_refund_btn(frm)
	}
})

function set_norek_btn(frm){
    if(frappe.user.has_role("CSD")){
        frm.add_custom_button(__('Get Dx Rex'), function(){-
			frappe.db.get_doc("Dx", frm.doc.dx_user).then(DxDoc=>{
				if(!DxDoc){
					frappe.msgprint("Not found", "Error")
					return
				}
				var v = DxDoc
				var rstr = "<table class='dxtable' >"
				$.each(v.rek || [], function(i, r) {
					rstr += "<table><tr><td>" + r.no_rek +"</td></tr>"
					rstr += "<tr><td>" + r.nama_rek +"</td></tr>"
					rstr += "<tr><td>" + r.bank +"</td></tr></table>"
					rstr += "<p>--------------------------</p><p></p>"
				})
				rstr += "<p></p>"
				frappe.msgprint(rstr+"<tableclass='dxtable'><tr><td>Sal :&nbsp</td><td>" + v.saldo +"</td></tr><table class='dxtable'><tr><td>IS id   :&nbsp</td><td>"+ (v.is_id || "-") +'</td><td>','Dx');

				$('table.dxtable > tr > th').css('padding', '2px')
				$('table.dxtable > tr > td').css('padding', '2px')
			})
            // frappe.db.get_value("Dx", {"name": frm.doc.dx_user},["rek", "saldo","is_id"], function(v) {});
        });
        frm.add_custom_button(__('Go Dx'), function(){
            frappe.set_route("Form", "Dx", frm.doc.dx_user)
		});
		if(frm.doc.cash_transfer == "Transfer"){
			frm.add_custom_button(__('Book'), function(){				
				frappe.call({
					method: "bo.bo.doctype.dppu.dppu.book_transfer",
					args: {						
						"docname": frm.doc.name
					},
					callback: function(r) {
						if (r.message) {							
							if(r.message.status == "Success"){
								frappe.set_route("Form", "Dx", frm.doc.dx_user)
							} else if(r.message.status == "Booked"){
								frappe.msgprint("already book on : " + r.message.date, "Booked")
							}
							// if (r.message[party_field]) frm.set_value(party_field, r.message[party_field]);
							// if (r.message.project) frm.set_value("project", r.message.project);
							// if (r.message.grand_total) frm.set_value("amount", r.message.grand_total);
						}
					}
				});
			});
		}
    }
}

function set_refund_btn(frm){
    //if((frappe.user.has_role("ARCO") || frappe.user.has_role("Account Manager")) && frm.doc.amount_refund ){
        frm.add_custom_button(__('R fun'), function(){			
			frappe.call({
				method: 'bo.bo.doctype.dppu.dppu.refund',
				args: {
					"docname": frm.doc.name
				},
				callback: function(r) {
					if (!r.exc) {
						if(r.message.status == "Success"){
							frappe.set_route("Form", "Dx", frm.doc.dx_user)
						} else if(r.message.status == "Refunded"){
							frappe.msgprint("Refund is made on : " + r.message.date, "Refunded")
						} else {
							frappe.msgprint(r.message.status, "Refund")
						}
					}
				}
			});
        });
    // }
}

function set_filter(frm){
    if(frappe.user.has_role("DM") && frappe.user.name != "Administrator"){
          frm.set_value("dm_user", "DM-" + frappe.session.user.replace(/@.*/g,"").toUpperCase())
          frappe.db.get_value("DM",frm.doc.dm_user,["territory","sm_user"],function(res){
              if(res != undefined){
				frm.set_value("territory", res.territory)
				frm.set_value("sm_user", res.sm_user)
              }else {
                //frappe.msgprint("You may not have a DM role, not allowed !")
              } 
          })
    }      
    if(frm.doc.dm_user){
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


function set_color_saldo(frm){
	if(frm.doc.saldo < 0){
		// $("[data-fieldname='saldo']>div>.control-input-wrapper").css({color:"red"})
		$("[data-fieldname='saldo']>div>.control-input-wrapper>.control-value").css({"background-color":"red","color":"white"})
	}
}