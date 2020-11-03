// Copyright (c) 2020, Sistem Koperasi and contributors
// For license information, please see license.txt
var comid = 0;
var username = frappe.session.user.replace(/@.*/g,"").toUpperCase()
var ppn = 1.1;

frappe.ui.form.on('DPL', {
    onload: function(frm){
        if(frappe.user.has_role("DM")){
            frappe.db.get_value("DM","DM-"+username,["territory","comid"],function(res){
              if(res != undefined){
				comid = res.comid
				set_filter_by_comid(frm, res.comid)
              }
            })
        }
    },
	refresh: function(frm) {
	    set_parseXls_btn(frm)
	},
	year: function(frm){
	    set_start_end_date(frm)
	},
	month: function(frm){
		set_start_end_date(frm)
	},
	start_date: function(frm){
	   // frm.set_value("month_code", moment(frm.doc.start_date).format("YYMM"))
	},
	outid: function(frm){
	    frm.set_value("outlet_name", frm.doc.outid.replace(/^.*-/g,""))
		frm.set_value("is_outlet_id", frm.doc.outid.match(/^[0-9_]+/g)[0])
	},
	distributor: function(frm){
		let dist_outlet = frm.doc.distributor.toLowerCase() + "_outlet_name"
		let dist_outid = frm.doc.distributor.toLowerCase() + "_outid"
		frappe.db.get_value("Outlet",frm.doc.outid,[dist_outlet, dist_outid],function(res){
			if(res != undefined){
				frm.set_value("dist_outlet_name", res[dist_outlet])
				frm.set_value("dist_outid", res[dist_outid])
			}
	   })
	},
	line: function(frm){
	    if(frm.doc.line == "")
			return
		// let distributor = frm.doc.distributor.toLowerCase()
		// var items = frappe.db.get_list("Item", {filters:{"line":frm.doc.line},fields: ["item_code","item_name","standard_rate",distributor +"_item_code",distributor +"_item_name"], limit: 200})
		// items.then((list)=>{
		//     list.forEach((o,i)=>{
		//         var ch = frm.add_child('items')
		//         ch.item_code = o.item_code
		// 		ch.item_name = o.item_name
		// 		ch.ppg_item_code = o.ppg_item_code
		// 		ch.ppg_item_name = o.ppg_item_name
		//         ch.hna = o.standard_rate
		//         ch.line = frm.doc.line
		//     })
		//     frm.refresh_field('items');
		// })
	}
})

frappe.ui.form.on('DPL Item', {
	refresh(frm) {

	},
	item_code: function(frm, dt, dn) {
		let o = locals[dt][dn];
		// frm.doc[o.parentfield][o.idx-1].add_fetch('hjm_sm','hjm_gsm','hjm_fin')
	},
	hna: function(frm, dt, dn) {
		calc_item(frm, dt, dn)
	},
	hna1: function(frm, dt, dn) {
		calc_item(frm, dt, dn)
	},
	dpl_disc: function(frm, dt, dn) {
		dpl_disc_calc(frm, dt, dn)
	},
	dpl_disc1: function(frm, dt, dn) {
		calc_item(frm, dt, dn)
	},
	off_faktur: function(frm, dt, dn) {
		calc_item(frm, dt, dn)
	}
})

function dpl_disc_calc(frm, dt, dn){
	let o = locals[dt][dn];
	// reset hna1
	frm.doc[o.parentfield][o.idx-1].hna1 = 0
	calc_item(frm, dt, dn)
}

function calc_item(frm, dt, dn){
	let o = locals[dt][dn];
	let dpl_disc = frm.doc[o.parentfield][o.idx-1].dpl_disc?frm.doc[o.parentfield][o.idx-1].dpl_disc/100:0
	if (frm.doc[o.parentfield][o.idx-1].hna1){
		dpl_disc = 1-frm.doc[o.parentfield][o.idx-1].hna1 /frm.doc[o.parentfield][o.idx-1].hna
		frm.doc[o.parentfield][o.idx-1].dpl_disc = dpl_disc * 100
	} else {
		frm.doc[o.parentfield][o.idx-1].hna1 =  frm.doc[o.parentfield][o.idx-1].hna * (1-dpl_disc)
	}

	let dpl_disc1 = frm.doc[o.parentfield][o.idx-1].dpl_disc1/100
	let disc_off = frm.doc[o.parentfield][o.idx-1].off_faktur/100
	let total_disc = 1 - (1-dpl_disc) * (1-dpl_disc1) * (1-disc_off)

	var nf = Intl.NumberFormat('id-ID');
	frm.doc[o.parentfield][o.idx-1].total_disc = (total_disc * 100).toFixed(2)
	frm.doc[o.parentfield][o.idx-1].nsv1_ppn = nf.format((frm.doc[o.parentfield][o.idx-1].hna * (1-dpl_disc) * (1-dpl_disc1) * ppn).toFixed(0))
	frm.doc[o.parentfield][o.idx-1].nsv2_ppn = nf.format((frm.doc[o.parentfield][o.idx-1].hna * (1-dpl_disc) * (1-dpl_disc1) * (1-disc_off) * ppn).toFixed(0))

	frm.refresh_field(o.parentfield)
}
function set_start_end_date(frm){
	if(frm.doc.month){
		frm.set_value("month_code", frm.doc.year.substring(2) + frm.doc.month)
		var m = moment({year:frm.doc.year, month: cint(frm.doc.month) - 1})
		frm.set_value("start_date", frm.doc.year + "-" + frm.doc.month + "-01" )
		frm.set_value("end_date", m.endOf('month').format('YYYY-MM-DD'))
	} else {
		frm.set_value("month_code", "")
		frm.set_value("start_date", "")
		frm.set_value("end_date", "")
	}
}

function set_filter_by_territory(frm, territory){
    for(var i=1;i<=10;i++){
        frm.set_query("d"+i, function(doc) {
			return {
				filters: {
					'territory': territory
				}
			};
		});
    }
    frm.set_query("outid", function(doc) {
		return {
			filters: {
				'territory': territory
			}
		};
	});
}

function set_filter_by_comid(frm, comid){
    frm.set_query("outid", function(doc) {
		return {
			filters: {
				'comid': comid
			}
		};
	});
}

function set_parseXls_btn(frm){
    frm.add_custom_button(__('Get XLS'), function(){
        frm.call('parseXLS').then((res) => {
				console.log(res)
				if(res != undefined){
				    if(res.message.data){
				        frm.doc.items.splice(frm.doc.items[0])
				        for(let i = 0; i < res.message.data.length; i++){
				            var dat = res.message.data[i]
				            var startEl = 10
				            var rowNotEmpty = dat.slice(startEl).find(el=>el>0)
				            if(rowNotEmpty){
    				            var ch = frm.add_child('items')
                		        ch.item_code = dat[7]
                		        ch.item_name = dat[8]
                		        ch.hna = dat[9]
                		        ch.dpl_disc = dat[10]
				            }
				        }
				        frm.refresh_field('items')
				    }
				}
			});
    });
    frm.add_custom_button(__('Download XLS'), function(){
        var method = '/api/method/bo.bo.doctype.dpl.dpl.download_template';
        var filters = [['name','=', frm.docname]];
        open_url_post(method, {
			doctype: frm.doctype,
			file_type: "Excel",
			export_fields: {"DPL":["name","outid","month","year","distributor","line","is_outlet_id"],"items":["name","item_code","item_name","hna","dpl_disc"]},
			export_filters: filters,
			export_protect_area: [2, 11, 12],
		});
	});

	frm.add_custom_button(__('Dwnld Distro XLS'), function(){
        var method = '/api/method/bo.bo.doctype.dpl.dpl.download_template';
		var distributor = frm.doc.distributor.toLowerCase()
		var dpl_extras = [ distributor+"_outid" ]
		var item_extras = [distributor +"_item_code", distributor +"_item_name" ]
        var filters = [['name','=', frm.docname]];
        open_url_post(method, {
			doctype: frm.doctype,
			file_type: "Excel",
			export_fields: {"DPL":["name","outid", "start_date", "end_date", "distributor","line","is_outlet_id"].concat(dpl_extras),"items":["name","item_code","item_name","hna","dpl_disc"].concat(item_extras)},
			export_filters: filters,
			export_protect_area: [2, 12, 13],
		});
    });
}

function download_template(frm) {
		frappe.require('/assets/js/data_import_tools.min.js', () => {
			frm.data_exporter = new frappe.data_import.DataExporter(
				"DPL",
				"Insert New Records"
			);
		});
	}
