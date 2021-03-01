// Copyright (c) 2020, Sistem Koperasi and contributors
// For license information, please see license.txt

frappe.ui.form.on('DPPU', {
    onload: function(frm){
		set_filter(frm)
		set_color_saldo(frm)
		check_state_warning(frm)
		// check_booked(frm)
	},
	onload_post_render: function(frm){
		check_booked(frm)
		if(frm.doc.workflow_state == "CSD Received"){
			frappe.show_alert('Hi, Do not forget to check the date !', 5);
			disable_workflow("Approve")
			$("[data-fieldname='date']").click((function(e){
				frm.states.show_actions()
			}).bind(frm))
		}
	},
    refresh: function(frm){
		set_norek_btn(frm)
		set_color_saldo(frm)
		set_refund_btn(frm)
    },
    validate: function(frm){
		var allowed_states = ["Overdue Refund","DM Recap","Refund"]
        if (frm.doc.date < frappe.datetime.get_today() && !allowed_states.includes(frm.doc.workflow_state)) {
            frappe.msgprint(__("You can not select past date in From Date"));
            frappe.validated = false;
		}
	},
	before_workflow_action: function(frm){ //before_workflow_action
		// if((frm.doc.workflow_state == "FIN Approved")
		// 	&& (frappe.user.has_role("CSD")||frappe.user.has_role("Accounts Manager"))){
		// 	var status = bookDx(frm, 1)
		// 	if(!status){
		// 		frappe.validated = false;
		// 		frappe.throw("Not yet Booked")
		// 		frm.disable_save();
		// 	}else{
		// 		frm.enable_save();
		// 	};
		// }
	},
	amount_refund: function(frm){
		if(frm.doc.amount_refund > frm.doc.number){
			frm.set_value('amount_refund', frm.doc.number)
			frappe.msgprint(__("Cannot input the amount greater than Number !"), "Error");
		}
		set_refund_btn(frm)
	},
	number: function(frm){
		let line = frm.doc.mr_user.match(/(?<=_)\w+$/gi)[0].toLowerCase() //frm.doc.mr_user.substr(-1)
		var delta = frm.doc['saldo_' + line] - frm.doc.number
		if(delta < 0){
			console.log("Exceeding saldo")
		}
	},
	number_part: function(frm){
		let number_part = frm.doc.number_part.replaceAll(' ','').replaceAll('.',',').split(',').map(o=>cint(o))
		frm.set_value('number', number_part.reduce((a,v)=>a+v))
		var delta = frm.doc['saldo'] - frm.doc.number
		if(delta < 0){
			console.log("Exceeding saldo")
		}
	},
	jml_ccln: function(frm){
		if(frm.doc.jml_ccln){
			let line = frm.doc.mr_user.match(/(?<=_)\w+$/gi)[0].toLowerCase()
			var delta = frm.doc['saldo_' + line] - frm.doc.number
			if(delta >= -10000 && parseInt(frm.doc.jml_ccln) > 6){ // BO18->BO28
				frm.set_value("jml_ccln", "6")
			} else if(delta < -10000 && delta >= -20000 && parseInt(frm.doc.jml_ccln) > 9) {
				frm.set_value("jml_ccln", "9")
			} else if(delta < -20000 && parseInt(frm.doc.jml_ccln) > 12) {
				frm.set_value("jml_ccln", "12")
			}
		}
	}
})

function check_booked(frm){
	if((frm.doc.workflow_state == "FIN Approved")
		&& (frappe.user.has_role("CSD")||frappe.user.has_role("Accounts Manager"))){
		if(frm.doc.jml_ccln)
			bookAdvDx(frm, 1)
		else
			bookDx(frm, 1)
	}
}

function set_norek_btn(frm){
    if(frappe.user.has_role("CSD")){
        frm.add_custom_button(__('Get Dx Rex'), function(){
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
		if((frm.doc.workflow_state == "FIN Approved" || frm.doc.workflow_state == "CSD Transferred" || frm.doc.workflow_state == "DM Received" )
			&& (frappe.user.has_role("CSD")||frappe.user.has_role("Accounts Manager"))){
			if(frm.doc.jml_ccln){
				frm.add_custom_button(__('Adv Book'), function(){
					bookAdvDx(frm, 0)
				});
			} else {
				frm.add_custom_button(__('Book'), function(){
					bookDx(frm, 0)
				});
			}
		}
    }
}

function bookDx(frm, check){
	frm.enable_save();
	frm.states.show_actions()
	frappe.call({
		method: "bo.bo.doctype.dppu.dppu.book_transfer",
		args: {
			"docname": frm.doc.name,
			"check": check
		},
		callback: function(r) {
			if (r.message) {
				if(r.message.status == "Success"){
					frappe.set_route("Form", "Dx", frm.doc.dx_user)
				} else if(r.message.status == "Booked"){
					frappe.msgprint("already book on : " + r.message.date, "Booked")
				} else if(r.message.status == "No Book Record"){
					frappe.msgprint("No Book Record !, click Book", "Not Booked")
					frappe.validated = false;
					frm.disable_save();
					disable_workflow("Approve")
					disable_workflow("Send")
				}
			}
		}
	});
}

function bookAdvDx(frm, check){
	frm.enable_save();
	frm.states.show_actions()
	frappe.call({
		method: "bo.bo.doctype.dppu.dppu.adv_transfer",
		args: {
			"docname": frm.doc.name,
			"check": check
		},
		callback: function(r) {
			if (r.message) {
				if(r.message.status == "Success"){
					frappe.set_route("Form", "Dx", frm.doc.dx_user)
				} else if(r.message.status == "Booked"){
					frappe.msgprint("already book on : " + r.message.date, "Adv")
				} else if(r.message.status == "Saldo is sufficient"){
					frappe.msgprint("Sal is sufficcient, no need Adv", "Adv")
				} else if(r.message.status == "Jml Ccln is empty, No Adv DPPU"){
					frappe.msgprint("Jml Ccln is empty, No Adv DPPU", "Adv")
				} else if(r.message.status == "No Book Record"){
					frappe.msgprint("No Adv Book Record !, click Adv Book", "Adv Not Booked")
					frappe.validated = false;
					frm.disable_save();
					disable_workflow("Approve")
					disable_workflow("Send")
				}
			}
		}
	});
}

function set_refund_btn(frm){
    if((frappe.user.has_role("ARCO") || frappe.user.has_role("Accounts Manager")) && frm.doc.amount_refund ){
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
    }
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

function check_state_warning(frm){
	if(frappe.user.has_role("CSD") || frappe.user.has_role("Accounts Manager")|| frappe.user.has_role("Accounts User")){
		frappe.db.get_list("DPPU", {filters:{"dm_user":frm.doc.dm_user,"workflow_state" : ['in',["DM Received","Refund"]]},fields: ["workflow_state","name","number"], limit: 20}).then((d)=>{
			if(d.length > 0){
				var str = ''
				var sum = 0
				d.forEach(e => {
					str += '<tr><td>'+e.name+'</td><td>'+e.workflow_state+'</td><td>'+e.number+'</td></tr>'
					sum += e.number
				});
				if (d.length > 3){
					str = '<table class="table" id="dppu-records" style="color:red"><tbody>'+str+ '<tr><td></td><td>Sum:</td><td>'+sum+'</td></tr></tbody></table>'
					frappe.msgprint({
						"title": "Not Eligible",
						"message": str,
						"indicator": "red"
					})
				}else{
					str = '<table class="table" id="dppu-records"><tbody>'+str+ '<tr><td></td><td>Sum:</td><td>'+sum+'</td></tr></tbody></table>'
					frappe.msgprint(str, "Active DPPU")
				}
				// $(".form-page").prepend(str)
			} else{
				$("#dppu-records").remove()
			}
		})
	}
}


function set_color_saldo(frm){
	let line = frm.doc.mr_user.match(/(?<=_)\w+$/gi)[0].toLowerCase()
	if(frm.doc['saldo_' + line] < 0){
		$("[data-fieldname='saldo']>div>.control-input-wrapper>.control-value").css({"background-color":"red","color":"white"})
	}
}

function disable_workflow(name){
	$(`[data-label='${name}']`).css("color", "lightgrey")
	$(`[data-label='${name}']`).parent().off()
}