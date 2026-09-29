// Copyright (c) 2020, Sistem Koperasi and contributors
// For license information, please see license.txt
var comid = 0;
var username = frappe.user.full_name()
var ppn = 1.11;
var old_outid = null

frappe.ui.form.on('DPL', {
	onload: function(frm){
		// load_org_code(frm)
	},
	onload_post_render(frm){
		set_DM(frm)
		paint_over_hjm(frm)
	},
	refresh: function(frm) {
	    set_parseXls_btn(frm)
		set_download_xls_apl(frm)
		set_show_hjm(frm)
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
	type: function(frm){
	  set_readonly_fixed_price(frm)
	},
	org_code:function(frm){
		old_outid = null
	},
	distributor: function(frm){
		load_org_code(frm)	
	},
	line: function(frm){
		// frappe.validated = true;
		set_DM(frm)		
	}
})

const dfunc = (frm, dt, dn) => {
	let o = locals[dt][dn]
	calc_item(frm, o)
}

frappe.ui.form.on('DPL Item', {
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

function get_over_hjm_flag(o, frm) {
    if (o.hna1_ppn < o.hjm_fin) {
        return 3; // Finance limit exceeded
    } else if (o.hna1_ppn < o.hjm_gsm  && frm.doc.over_hjm < 2) {
        return 2; // GSM limit exceeded
    } else if (o.hna1_ppn < o.hjm_sm  && frm.doc.over_hjm < 1) {
        return 1; // SM limit exceeded
    }
    return 0; // within limits
}


function calc_item(frm, o) {
    let dc = frm.doc[o.parentfield][o.idx - 1];
    let disc_rate = dc.dpl_disc ? dc.dpl_disc / 100 : 0;

    if (dc.hna) {
        disc_rate = 1 - dc.hna / dc.hna0;
        dc.dpl_disc = disc_rate * 100;
    } else {
        dc.hna = dc.hna0 * (1 - disc_rate);
    }

    let extra_disc = dc.dpl_disc1 / 100;
    let total_disc_rate = 1 - (1 - disc_rate) * (1 - extra_disc);

    dc.hna1 = dc.hna0 * (1 - total_disc_rate);
    dc.hna_ppn = flt((dc.hna0 * (1 - disc_rate) * ppn).toFixed(0));
    dc.hna1_ppn = flt((dc.hna1 * ppn).toFixed(0));
    dc.total_disc = flt(100 * total_disc_rate, 2);

    // Uniform flagging using hna1_ppn	
    frm.doc.over_hjm = get_over_hjm_flag(dc, frm);

    try { paint_over_hjm(frm); } catch (error) { console.log(error); }
    try { paint_over_hjm_item(frm, o); } catch (error) { console.log(error); }

    frm.refresh_field(o.parentfield);
	frm.refresh_field('over_hjm');
}

function isOverHJM(o) {
    return (
        (frappe.user.has_role("SM") && o.hna1_ppn < o.hjm_sm) ||
        (frappe.user.has_role("GSM") && o.hna1_ppn < o.hjm_gsm) ||
        (frappe.user.has_role("Accounts Manager") && o.hna1_ppn < o.hjm_fin)
    );
}

function paint_over_hjm(frm) {
    frm.doc.items.forEach(o => {
        let row = cur_frm.fields_dict.items.grid.grid_rows[o.idx - 1].row_index;
        row.css({"background-color": isOverHJM(o) ? "#ffcccc" : "#fff"});
    });
}

function paint_over_hjm_item(frm, o) {
    let field = frappe.ui.form.get_open_grid_form().grid_form.fields_dict.hna1_ppn.$input_wrapper;
    field.css({'color': isOverHJM(o) ? '#f00' : '#36414c'});
}



// function calc_item(frm, o){
// 	let dc = frm.doc[o.parentfield][o.idx-1]
// 	let dpl_disc = dc.dpl_disc?dc.dpl_disc/100:0
// 	if (dc.hna){
// 		dpl_disc = 1-dc.hna /dc.hna0
// 		dc.dpl_disc = dpl_disc * 100
// 	} else {
// 		dc.hna =  dc.hna0 * (1-dpl_disc)
// 	}

// 	let dpl_disc1 = dc.dpl_disc1/100
// 	var total_disc = 1 - (1-dpl_disc) * (1-dpl_disc1)
// 	dc.hna1 =  dc.hna0 * (1-total_disc)

// 	var nf = Intl.NumberFormat('id-ID'); //nf.format(
// 	dc.hna_ppn = flt((dc.hna0 * (1-dpl_disc) * ppn).toFixed(0))
// 	dc.hna1_ppn = flt((dc.hna1 * ppn).toFixed(0))
// 	dc.total_disc = flt((100 * total_disc), 2)

// 	let hjm_sm = dc.hjm_sm
// 	let hjm_gsm = dc.hjm_gsm
// 	let hjm_fin = dc.hjm_fin

// 	if (dc.dpl_disc1 > hjm_fin){
// 		frm.set_value("over_hjm", 3)
// 	} else if(dc.dpl_disc1 < hjm_fin && dc.dpl_disc1 > hjm_gsm && frm.doc.over_hjm < 2){
// 		frm.set_value("over_hjm", 2)
// 	} else if(dc.dpl_disc1 < hjm_gsm && dc.dpl_disc1 > hjm_sm && frm.doc.over_hjm < 1){
// 		frm.set_value("over_hjm", 1)
// 	} else frm.set_value("over_hjm", 0)

// 	try {
// 		paint_over_hjm(frm)
// 	}catch(error){console.log(error)}
// 	try {
// 		paint_over_hjm_item(frm, o)
// 	}catch(error){console.log(error)}

// 	frm.refresh_field(o.parentfield)
// }

// function paint_over_hjm(frm){
// 	frm.doc.items.forEach(o=>{
// 		if(frappe.user.has_role("SM") && o.hna1_ppn < o.hjm_sm * o.hna * ppn
// 		|| frappe.user.has_role("GSM") && o.hna1_ppn < o.hjm_gsm * o.hna * ppn
// 		|| frappe.user.has_role("Accounts Manager") && o.hna1_ppn < o.hjm_sm * o.hna * ppn){
// 			cur_frm.fields_dict.items.grid.grid_rows[o.idx-1].row_index.css({"background-color":"#ffcccc"})
// 		} else{
// 			cur_frm.fields_dict.items.grid.grid_rows[o.idx-1].row_index.css({"background-color":"#fff"})
// 		}
// 	})
// }

// function paint_over_hjm_item(frm, o){	
// 	if(frappe.user.has_role("SM") && o.hna1_ppn < o.hjm_sm * o.hna * ppn
// 	|| frappe.user.has_role("GSM") && o.hna1_ppn < o.hjm_gsm * o.hna * ppn
// 	|| frappe.user.has_role("Accounts Manager") && o.hna1_ppn < o.hjm_sm * o.hna * ppn){
// 		frappe.ui.form.get_open_grid_form().grid_form.fields_dict.hna1_ppn.$input_wrapper.css({'color':'#f00'})
// 	} else{
// 		frappe.ui.form.get_open_grid_form().grid_form.fields_dict.hna1_ppn.$input_wrapper.css({'color':'#f00'}).css({'color':'#36414c'})
// 	}
// }


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


function set_download_xls_apl(frm){
	if (!frm.is_new() && frm.doc.distributor) {
		frm.add_custom_button('APL Excel', () => {
			// Adjust the method path based on where you saved your python script
			let method_path = 'bo.bo.doctype.dpl.generate_dpl_excel'; 
			
			let url = frappe.urllib.get_full_url(
				`/api/method/${method_path}?docname=${encodeURIComponent(frm.doc.name)}`
			);
			window.open(url, '_blank');
		}, 'Actions');
	}
}

function set_show_hjm(frm){
	// if (frappe.user.has_role('System Manager') || frappe.user.has_role('Account Manager')) {
		frm.add_custom_button(__('Show HJM List'), function() {
			// Build HTML table dynamically
			let rows = frm.doc.items.map(item => {
				return `
					<tr>
						<td>${item.item_code || ''}</td>
						<td>${item.hjm_sm || ''}</td>
						<td>${item.hjm_gsm || ''}</td>
						<td>${item.hjm_fin || ''}</td>
					</tr>
				`;
			}).join('');

			let html = `
				<table class="table table-bordered">
					<thead>
						<tr>
							<th>Item Code</th>
							<th>HJM SM</th>
							<th>HJM GSM</th>
							<th>HJM FIN</th>
						</tr>
					</thead>
					<tbody>
						${rows}
					</tbody>
				</table>
			`;

			// Create dialog
			let d = new frappe.ui.Dialog({
				title: __('HJM Values for Items'),
				fields: [
					{
						fieldtype: 'HTML',
						fieldname: 'hjm_table',
						options: html
					}
				],
				primary_action_label: __('Close'),
				primary_action: function() {
					d.hide();
				}
			});

			d.show();
		});
	// }
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
			export_fields: {"DPL":["name","outid","month","year","distributor","line"],"items":["name","item_code","item_name","hna","dpl_disc", "hna1", "dpl_disc1","hna1_ppn", "total_disc"]},
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
			export_fields: {"DPL":["name","outid", "start_date", "end_date", "distributor","line"].concat(dpl_extras),"items":["name","item_code","item_name","hna","dpl_disc","hna1","dpl_disc1","hna1_ppn"].concat(item_extras)},
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