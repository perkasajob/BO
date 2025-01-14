// Copyright (c) 2020, Sistem Koperasi and contributors
// For license information, please see license.txt
var comid = 0;
// var username = frappe.session.user.replace(/@.*/g,"").toUpperCase()
var username = frappe.user.full_name()
var ppn = 1.11;
var old_outid = null

frappe.ui.form.on('DPF', {
	onload: function(frm){
		load_org_code(frm)
		// set_readonly_fixed_price(frm)
	},
	onload_post_render(frm){
		set_DM(frm)
		paint_over_hjm(frm)
		frm.fields_dict.outid.$input.on('input', function (e) {
			let val = e.target.value
			if(val.length > 2 && !val.startsWith(old_outid)){ // pull list
				load_outid(frm, val)
				old_outid = val
			}
		}).on('awesomplete-selectcomplete', function(e){
			try {
				frm.set_value('outid', e.target.value)
				if(frm?.var?.outlets !== undefined
					&& frm.var.outlets[e.target.value] !== undefined ){
						console.log(frm.var.outlets[e.target.value])
					frm.set_value("outlet_name", frm.var.outlets[e.target.value].name)
					frm.set_value("outlet_address", frm.var.outlets[e.target.value].address)
					frm.set_value("outlet_type", frm.var.outlets[e.target.value].sales_chn)
				}
			} catch (error) {console.log(error)}
		})
	},
	refresh: function(frm) {
	    set_parseXls_btn(frm)
	},
	validate(frm){
		if(!frm.doc.dm){
			frappe.validated = false;
			frappe.msgprint('DM cannot be empty !')
		}
		if(frm.doc.type == 'DPF'){
			$.each(frm.doc.items || [], function(i, d) {
				if(!d.qty) {
					frappe.validated = false;
					frappe.msgprint('Item Qty cannot be empty for DPF!')
				}
			})
		}
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
	type: function(frm){
	  set_readonly_fixed_price(frm)
	},
	org_code:function(frm){
		old_outid = null
	},
	distributor: function(frm){
		load_org_code(frm)
		// let dist_outlet = frm.doc.distributor.toLowerCase() + "_outlet_name"
		// let dist_outid = frm.doc.distributor.toLowerCase() + "_outid"
		// frappe.db.get_value("Outlet",frm.doc.outid,[dist_outlet, dist_outid],function(res){
		// 	if(res != undefined){
		// 		frm.set_value("dist_outlet_name", res[dist_outlet])
		// 		frm.set_value("dist_outid", res[dist_outid])
		// 	}
	  //  })
	},
	line: function(frm){
		// frappe.validated = true;
		set_DM(frm)
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

const dfunc = (frm, dt, dn) => {
	let o = locals[dt][dn]
	calc_item(frm, o)
}

frappe.ui.form.on('DPF Item', {
	form_render(frm, dt, dn){
		setTimeout(paint_over_hjm_item, 3000, frm, locals[dt][dn]);
	},
	item_code: dfunc,
	hna: dfunc,
	dpl_disc: dfunc,
	hna1: dfunc,
	dpl_disc1: dfunc
})

function set_DM(frm){
	if(frappe.user.has_role("DM") && frappe.user.name != "Administrator"){
		frappe.db.get_value('MP', {line: frm.doc.line, full_name: frappe.user.full_name()}, 'name')
		.then(r => {
			if(r.message?.name){
				frm.set_value("dm", r.message.name)
			} else {frappe.msgprint(frappe.user.full_name() + " not found in MP " + frm.doc.line)}
		})
	}
}

function dpl_disc_calc(frm, dt, dn){
	let o = locals[dt][dn];
	// reset hna2
	frm.doc[o.parentfield][o.idx-1].hna2 = 0
	calc_item(frm, dt, dn)
}

function calc_item(frm, o){
	let dc = frm.doc[o.parentfield][o.idx-1]
	let dpl_disc = dc.dpl_disc?dc.dpl_disc/100:0
	if (dc.hna){
		dpl_disc = 1-dc.hna /dc.hna0
		dc.dpl_disc = dpl_disc * 100
	} else {
		dc.hna =  dc.hna0 * (1-dpl_disc)
	}

	let dpl_disc1 = dc.dpl_disc1/100
	var total_disc = 1 - (1-dpl_disc) * (1-dpl_disc1)
	dc.hna1 =  dc.hna0 * (1-total_disc)

	var nf = Intl.NumberFormat('id-ID'); //nf.format(
	dc.hna_ppn = flt((dc.hna0 * (1-dpl_disc) * ppn).toFixed(0))
	dc.hna1_ppn = flt((dc.hna1 * ppn).toFixed(0))
	dc.total_disc = flt((100 * total_disc), 2)

	let hjm_1 = dc.hjm_1
	let hjm_2 = dc.hjm_2
	let hjm_3 = dc.hjm_3

	if (dc.dpl_disc > hjm_3){
		frm.set_value("over_hjm", 3)
	} else if(dc.dpl_disc < hjm_3 && dc.dpl_disc > hjm_2 && frm.doc.over_hjm < 2){
		frm.set_value("over_hjm", 2)
	} else if(dc.dpl_disc < hjm_2 && dc.dpl_disc > hjm_1 && frm.doc.over_hjm < 1){
		frm.set_value("over_hjm", 1)
	} else frm.set_value("over_hjm", 0)

	try {
		paint_over_hjm(frm)
	}catch(error){console.log(error)}
	try {
		paint_over_hjm_item(frm, o)
	}catch(error){console.log(error)}

	// frappe.db.get_value('Item', dc.item_code, ['hjm_1','hjm_2','hjm_3'], function(res){
	// 	if(res != undefined){
	// 		let total_disc = dc.total_disc
	// 		if([res.hjm_1, res.hjm_2, res.hjm_3].every(o=> o > 0)){
	// 			set_total_disc_color(frm, total_disc, res)
	// 		}
	// 	}
	// })
	frm.refresh_field(o.parentfield)
}

function paint_over_hjm(frm){
	frm.doc.items.forEach(o=>{
		if(frappe.user.has_role("SM") && o.hna1_ppn < o.hjm_1
		|| frappe.user.has_role("GSM") && o.hna1_ppn < o.hjm_2
		|| frappe.user.has_role("Accounts Manager") && o.hna1_ppn < o.hjm_1){
			// $("[data-fieldname='total_disc']>div>.control-input-wrapper>.control-value").css({"background-color":"red","color":"white"})
			// $(`[data-idx=${o.idx}] > .data-row > [data-fieldname=item_name]`).css('background-color', '#ffcccc');
			// frm.fields_dict.items.grid.grid_rows[o.idx-1].columns.item_code.css("background-color","#ffcccc")
			// frm.fields_dict.items.grid.grid_rows[o.idx-1].columns.item_name.css("background-color","#ffcccc")
			// cur_frm.fields_dict.items.grid.grid_rows[o.idx-1].grid_form.fields_dict.hna1_ppn.$input_wrapper.css({'color':'#f00'})
			cur_frm.fields_dict.items.grid.grid_rows[o.idx-1].row_index.css({"background-color":"#ffcccc"})
		} else{
			// $("[data-fieldname='total_disc']>div>.control-input-wrapper>.control-value").css({"background-color":"#f5f7fa","color":"black"})
			// frm.fields_dict.items.grid.grid_rows[o.idx-1].columns.item_code.css("background-color","#fff")
			// frm.fields_dict.items.grid.grid_rows[o.idx-1].columns.item_name.css("background-color","#ffcccc")
			// cur_frm.fields_dict.items.grid.grid_rows[o.idx-1].grid_form.fields_dict.hna1_ppn.$input_wrapper.css({'color':'#36414c'})
			cur_frm.fields_dict.items.grid.grid_rows[o.idx-1].row_index.css({"background-color":"#fff"})
		}
	})
}

function paint_over_hjm_item(frm, o){
	if(frappe.user.has_role("SM") && o.hna1_ppn < o.hjm_1
	|| frappe.user.has_role("GSM") && o.hna1_ppn < o.hjm_2
	|| frappe.user.has_role("Accounts Manager") && o.hna1_ppn < o.hjm_1){
		frappe.ui.form.get_open_grid_form().grid_form.fields_dict.hna1_ppn.$input_wrapper.css({'color':'#f00'})
	} else{
		frappe.ui.form.get_open_grid_form().grid_form.fields_dict.hna1_ppn.$input_wrapper.css({'color':'#f00'}).css({'color':'#36414c'})
	}
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

// function set_filter_by_territory(frm, territory){
//     for(var i=1;i<=10;i++){
//         frm.set_query("d"+i, function(doc) {
// 			return {
// 				filters: {
// 					'territory': territory
// 				}
// 			};
// 		});
//     }
//     frm.set_query("outid", function(doc) {
// 		return {
// 			filters: {
// 				'territory': territory
// 			}
// 		};
// 	});
// }

// function set_filter_by_comid(frm, comid){
//     frm.set_query("outid", function(doc) {
// 		return {
// 			filters: {
// 				'comid': comid
// 			}
// 		};
// 	});
// }

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
        var method = '/api/method/bo.bo.doctype.dpf.dpf.download_template';
        var filters = [['name','=', frm.docname]];
        open_url_post(method, {
			doctype: frm.doctype,
			file_type: "Excel",
			export_fields: {"DPF":["name","outid","month","year","distributor","line"],"items":["name","item_code","item_name","hna","dpl_disc", "hna1", "dpl_disc1","hna1_ppn", "total_disc"]},
			export_filters: filters,
			export_protect_area: [2, 11, 12],
		});
	});

	frm.add_custom_button(__('Dwnld Distro XLS'), function(){
        var method = '/api/method/bo.bo.doctype.dpf.dpf.download_template';
		var distributor = frm.doc.distributor.toLowerCase()
		var dpl_extras = [ distributor+"_outid" ]
		var item_extras = [distributor +"_item_code", distributor +"_item_name" ]
        var filters = [['name','=', frm.docname]];
        open_url_post(method, {
			doctype: frm.doctype,
			file_type: "Excel",
			export_fields: {"DPF":["name","outid", "start_date", "end_date", "distributor","line"].concat(dpl_extras),"items":["name","item_code","item_name","hna","dpl_disc","hna1","dpl_disc1","hna1_ppn"].concat(item_extras)},
			export_filters: filters,
			export_protect_area: [2, 12, 13],
		});
    });
}

function download_template(frm) {
		frappe.require('/assets/js/data_import_tools.min.js', () => {
			frm.data_exporter = new frappe.data_import.DataExporter(
				"DPF",
				"Insert New Records"
			);
		});
	}

function load_org_code(frm)	{``
	if(frm.doc.distributor && frm.doc.dm){
		frm.set_df_property("org_code", "options", []);

		frm.call('get_linked_org', { throw_if_missing: true })
			.then(r => {
					if (r.message) {
							let dist = r.message.split(',').join('\n');
							frm.set_df_property("org_code", "options", dist);
					}
			})
	}
}


function load_outid(frm, val){
	frappe.call({
		method: "bo.bo.bo_integration.tsj_integration.get_customers",
		args: {
			"orgCode": frm.doc.org_code,
			"customerName" : val,
		},
		callback: function(r) {
			if (r.results) {
				frm.set_value("outlet_name", "")
				frm.set_value("outlet_address", "")

				let outlets = {};
				r.results.forEach(o=>{
					outlets[o.value] = o
				})
				frm.var = {outid: r.results, outlets: outlets}
				let outid_list = r.results.map(o=>{
					let address = o.address ? ', '+ o.address: ''
					console.log(o.name + address)
					return {label: o.name + address , value: o.value}
				})
				outid_list = [ ...new Set(outid_list) ]
				frappe.show_alert(r.results.length + " Outlets loaded")
				console.log(outid_list.length + " Outlets loaded")
				if(frm.fields_dict.outid.awesomplete){
					frm.fields_dict.outid.awesomplete.destroy()
				}

				frm.fields_dict.outid.awesomplete = new Awesomplete(frm.fields_dict.outid.input, {
					list: outid_list,
					maxItems: 15,
				});
				frm.fields_dict.outid.input.focus()
				frm.fields_dict.outid.awesomplete.evaluate()
			}
		}
	});
}


// function set_readonly_fixed_price(frm){
// 	let editable = cur_frm.doc.type.substr(-11) == 'Fixed Price' ? 0: 1
// 	frm.fields_dict.items.grid.toggle_enable("dpl_disc", editable);
// }