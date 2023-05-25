// Copyright (c) 2023, Sistem Koperasi and contributors
// For license information, please see license.txt

frappe.ui.form.on('DPPU', {
	setup: function(frm) {
		frappe.db.get_doc('DPPU Settings')
			.then(settings => {
				frm.settings = settings
			})
	},
	onload: function(frm){
		set_filter(frm)
		check_state_warning(frm)
		select_sal_to_tp(frm)
	},
	onload_post_render: function(frm){
		set_DM(frm)
		check_booked(frm)
		if(frm.doc.workflow_state == "CSD Received"){
			frappe.show_alert('Hi, Do not forget to check the date !', 5);
			disable_workflow("Approve")
			$("[data-fieldname='date']").click((function(e){
				frm.states.show_actions()
			}).bind(frm))
		}

		if((frm.doc.workflow_state == "Approved 1" && frm.doc.approver_1_name === frappe.user.full_name())
		|| (frm.doc.workflow_state == "Approved 2" && frm.doc.approver_2_name === frappe.user.full_name())){
			disable_workflow("Approve")
		}

		if(["JV", "JV Closed"].includes(frm.doc.workflow_state)){
			frm.set_df_property("cash_transfer", "read_only",1)
			frm.set_df_property("date", "read_only",1)
			frm.set_df_property("comment", "read_only",1)
			frm.set_df_property("mss", "read_only", !frappe.user.has_role("MSS Manager"))
		}

	},
	refresh: function(frm){
		set_norek_btn(frm)
		set_refund_btn(frm)
		select_sal_to_tp(frm)
	},
	validate: function(frm){
		var allowed_states = ["Overdue Refund","DM Recap","Refund"]
        if (frm.doc.date < frappe.datetime.get_today() && !allowed_states.includes(frm.doc.workflow_state)) {
            frappe.msgprint(__("You can not select past date in From Date"));
            frappe.validated = false;
		}
		if (frm.doc.number < 1){
			frappe.msgprint(__("Number Cannot be 0 or minus"));
            frappe.validated = false;
		}
		if (frm.doc.number > frm.settings.limit_1 && !frm.doc.approver_2){
			frappe.msgprint(__("Approver 2 is required"));
            frappe.validated = false;
		}
	},
	before_workflow_action: async function(frm){
		console.log(frm.selected_workflow_action);
		// frappe.throw(__("PUT ERROR HERE"), "Error");
		frappe.validated = true;
		if((frm.doc.workflow_state == "FIN Approved")
			&& (frappe.user.has_role("CSD")||frappe.user.has_role("Accounts Manager"))){
				frappe.run_serially([
					() => {
					if(frm.doc.jml_ccln)
						checkBookAdvDx(frm, 1)
					else
						checkBookDx(frm, 1)
					if (!frappe.validated)
						throw("Error !")
				}]);
		}

		if(frm.doc.workflow_state == "Approved 1" && ![frm.doc.approver_3_name, frm.doc.approver_2_name].includes(frappe.user.full_name()))
			frappe.throw(__("User not allowed, only approver 2 or 3 !"), "Error");

		if(frm.doc.workflow_state == "Approved 2" && frm.doc.approver_3_name != frappe.user.full_name())
			frappe.throw(__("User not allowed, only approver 3 !"), "Error");

		if(frm.doc.workflow_state == "JV" && frm.doc.jv_note.length < 5)
				frappe.throw(__("JV Note cannot be empty !"), "Error");

		if(["DM Received", "DM Send Out", "DM Recap", "JV"].includes(frm.doc.workflow_state)
		 && frm.attachments.get_attachments().length == 0 )
			frappe.throw(__("Please Attach documents"), "Error");
	},
	line: function(frm){
		set_DM(frm)
	},
	territory: function(frm){
		set_filter(frm)
	},
	dm: function(frm){
		set_query_TP(frm)
	},
	amount_refund: function(frm){
		if(frm.doc.amount_refund > frm.doc.number){
			frm.set_value('amount_refund', frm.doc.number)
			frappe.msgprint(__("Cannot input the amount greater than Number !"), "Error");
		}
		set_refund_btn(frm)
	},
	number: function(frm){
		let line = frm.doc.line.replace('Line', 'ql').toLowerCase() //frm.doc.tp.substr(-1)
		var delta = frm.doc['saldo_' + line] - frm.doc.number
		if(delta < 0){
			console.log("Exceeding saldo")
		} else {
			frm.set_value("jml_ccln", "")
			frm.set_value("number_part", "")
		}
	},
	number_part: function(frm){
		let number_part = frm.doc.number_part.replaceAll(' ','').replaceAll('.',',').split(',').map(o=>cint(o))
		number_part = number_part.reduce((a,v)=>a+v)
		if (number_part < 1)
			return

		frm.set_value('number', number_part)
		var delta = frm.doc['saldo'] - frm.doc.number
		if(delta < 0){
			console.log("Exceeding saldo")
		} else {
			frm.set_value("jml_ccln", "")
			frm.set_value("number_part", "")
		}
	},
	cash_transfer: function(frm){
		if(frm.doc.cash_transfer == "SPP"){
			frm.set_value("jml_ccln", "")
			frm.set_value("number_part", "")
		}
	},
	jml_ccln: function(frm){
		if(frm.doc.jml_ccln){
			let line = frm.doc.line.replace('Line', 'ql').toLowerCase()
			var delta = frm.doc['saldo_' + line] - frm.doc.number
			if(delta >= -frm.settings.delta_jml_ccln_9 && parseInt(frm.doc.jml_ccln) > 6){ // BO18->BO28
				frm.set_value("jml_ccln", "6")
			} else if(delta < -frm.settings.delta_jml_ccln_9 && delta >= -frm.settings.delta_jml_ccln_12 && parseInt(frm.doc.jml_ccln) > 9) {
				frm.set_value("jml_ccln", "9")
			} else if(delta < -frm.settings.delta_jml_ccln_12 && parseInt(frm.doc.jml_ccln) > 12) {
				frm.set_value("jml_ccln", "12")
			}  else if(delta < -frm.settings.delta_jml_ccln_24 && parseInt(frm.doc.jml_ccln) > 24) { // Shierly:ada user butuh 24 bulan
				frm.set_value("jml_ccln", "24")
			}
		}
	},
	dx_user: function(frm){
		select_sal_to_tp(frm)
	},
	tp: function(frm){
		select_sal_to_tp(frm)
	}
})

function check_booked(frm){
	if((frm.doc.workflow_state == "FIN Approved")
		&& (frappe.user.has_role("CSD")||frappe.user.has_role("Accounts Manager"))){
		getBookStatus(frm)
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

function getBookStatus(frm){
	frappe.call({
		method: "bo.bo.doctype.dppu.dppu.get_book_status",
		args: {
			"docname": frm.doc.name
		},
		callback: function(r) {
			if (r.message) {
				if(r.message.status == "No Book Record"){
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
					enable_workflow("Send")
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

function checkBookDx(frm, check){
	return frappe.xcall("bo.bo.doctype.dppu.dppu.book_transfer", {
				"docname": frm.doc.name,
				"check": check
			}).then((r) => {
				if (r) {
					if(r.status == "Booked"){
						console.log("already book on : " + r.date, "Booked")
					} else if(r.status == "No Book Record"){
						frappe.validated = false;
						frm.disable_save();
						disable_workflow("Approve")
						disable_workflow("Send")
						frappe.throw("No Book Record !, click Book")
					}
				}
			})
}

function checkBookAdvDx(frm, check){
	return frappe.xcall("bo.bo.doctype.dppu.dppu.adv_transfer",{
			"docname": frm.doc.name,
			"check": check
		}).then((r) =>{
			if (r) {
				if(r.status == "Booked"){
					console.log("already book on : " + r.date)
				} else if(r.status == "Saldo is sufficient"){
					console.log("Sal is sufficcient, no need Adv")
				} else if(r.status == "Jml Ccln is empty, No Adv DPPU"){
					frappe.throw("Jml Ccln is empty, No Adv DPPU", "Adv")
					frappe.validated = false;
				} else if(r.status == "No Book Record"){
					frappe.validated = false;
					frm.disable_save();
					disable_workflow("Approve")
					disable_workflow("Send")
					frappe.throw("No Adv Book Record !, click Adv Book")
				}
			}
		})
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
					frappe.validated = false;
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
    // if(frappe.user.has_role("DM") && frappe.user.name != "Administrator"){
    //       frm.set_value("dm_user", "DM-" + frappe.session.user.replace(/@.*/g,"").toUpperCase())
		//   if(frm.doc.__islocal || !frm.doc.sm_user)
		// 	frappe.db.get_value("DM",frm.doc.dm_user,["territory","sm_user"],function(res){
		// 		if(res != undefined){
		// 			frm.set_value("territory", res.territory)
		// 			frm.set_value("sm_user", res.sm_user)
		// 		}else {
		// 			//frappe.msgprint("You may not have a DM role, not allowed !")
		// 		}
		// 	})
    // }
    if(frm.doc.dm){
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
		frappe.db.get_list("DPPU", {filters:{"dm":frm.doc.dm,"workflow_state" : ['in',["DM Received","Refund"]]},fields: ["workflow_state","name","number"], limit: 20}).then((d)=>{
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


function select_sal_to_tp(frm){
	let lines = ['ql1','ql2','ql3','n1']
	if(frm.doc.tp){
		let line = frm.doc.line.replace('Line', 'ql').toLowerCase()
		lines.forEach(l=>{
			if(l == line){
				$(`[data-fieldname='saldo_${l}']`).show()
				if(frm.doc['saldo_' + line] <= 0){
					$(`[data-fieldname='saldo_${l}']>div>.control-input-wrapper>.control-value, [data-fieldname='saldo']>div>.control-input-wrapper>.control-value`).css({"background-color":"red","color":"white"})
				} else {
					$(`[data-fieldname='saldo_${l}']>div>.control-input-wrapper>.control-value, [data-fieldname='saldo']>div>.control-input-wrapper>.control-value`).css({"background-color":"#f5f7fa","color":"black"})
				}
			} else $(`[data-fieldname='saldo_${l}']`).hide()
		})
	}
}

function disable_workflow(name){
	$(`[data-label='${name}']`).css("color", "lightgrey")
	$(`[data-label='${name}']`).parent().off()
}

function enable_workflow(name){
	$(`[data-label='${name}']`).css("color", "grey")
	$(`[data-label='${name}']`).parent().on()
}


function set_DM(frm){
	if(frappe.user.has_role("DM") && frappe.user.name != "Administrator" && frm.doc.docstatus == 0){
		frappe.db.get_value('MP', {line: frm.doc.line, full_name: frappe.user.full_name()}, 'name')
		.then(r => {
				if(r.message.name){
					frm.set_value("dm", r.message.name)
				} else {frappe.msgprint(`<b>${frappe.user.full_name()}</b> not found in MP ${frm.doc.line}`)}
		})
	}
}

function set_query_TP(frm){
	console.log(frm.doc.dm)
	frm.set_query("tp", function(doc) {
		return {
			filters: {
				'parent_mp': frm.doc.dm,
				'line': frm.doc.line,
				'active': 1
			}
		};
	})
}