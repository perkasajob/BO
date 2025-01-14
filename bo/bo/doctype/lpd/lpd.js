// Copyright (c) 2020, Sistem Koperasi and contributors
// For license information, please see license.txt

var username = frappe.session.user.replace(/@.*/g,"").toUpperCase()
var ppn = 1.11;

frappe.ui.form.on('LPD', {
    onload: function(frm){
        // if(frappe.user.has_role("DM")){
        //     frappe.db.get_value("DM","DM-"+username,"territory",function(res){
        //       if(res != undefined){
        //         frm.set_value("territory", res.territory)
        //         set_filter_by_territory(frm, res.territory)
        //       }
        //     })
        // }
    },
	refresh: function(frm) {
	    set_parseXls_btn(frm)
	},
	file: function(frm){
		console.log("a file is uploaded")
		parseXLS(frm);
	},
	year: function(frm){
	    //frm.set_value("start_date",moment(frm.doc.start_date).startOf("month"))
	    frm.set_value("month_code", frm.doc.year.substring(2) + frm.doc.month)
	},
	month: function(frm){
	    frm.set_value("month_code", frm.doc.year.substring(2) + frm.doc.month)
	},
	outid: function(frm){
	},
	start_date: function(frm){
	},
	line: function(frm){
	  // if(frm.doc.line == "")
	  //       return
		// var items = frappe.db.get_list("Item", {filters:{"line":frm.doc.line, "is_group": 1},fields: ["item_code","item_name","hna","hjm_1","hjm_2","hjm_3"], limit: 200})

		// items.then((list)=>{
		// 	list.forEach((o,i)=>{
		// 		var ch = frm.add_child('items')
		// 		ch.item_code = o.item_code
		// 		ch.item_name = o.item_name
		// 		ch.hna = o.hna
		// 		ch.hjm_1 = o.hjm_1
		// 		ch.hjm_2 = o.hjm_2
		// 		ch.hjm_3 = o.hjm_3
		// 	})
		//   frm.refresh_field('items');
		// })
	},
	items_on_form_rendered: function(frm, cdt, cdn){
		let row = locals[cdt][cdn]
		const $labels = $('div[data-fieldname="items"] div[data-fieldname^="d"] label');
		for (let i = 1; i <= 10; i++) {
			$labels.filter(function() {
					return $(this).text().trim() === `D${i}`;
			}).text(frm.doc[`d${i}`]);
		}
	}
})




const dfunc = (frm, cdt, cdn) => {
	let o = locals[dt][dn]
	updatePercentages(frm, o)
}

frappe.ui.form.on('LPD Item', {
	item_code: function(frm, dt, dn) {
		let row = locals[dt][dn];
		// frm.doc[o.parentfield][o.idx-1].add_fetch('hjm_sm','hjm_gsm','hjm_fin')
	},
	hna: function(frm, dt, dn) {
	},
	dpl: dfunc,
	d1: dfunc,
	d2: dfunc,
	d3: dfunc,
	d4: dfunc,
	d5: dfunc,
	d6: dfunc,
	d7: dfunc,
	d8: dfunc,
	d9: dfunc,
	d10: dfunc,
})


function updatePercentages(frm, o) {
	let total_off = 0;
	let values = {};

	// Collect all values from d1 to d10
	for (let i = 1; i <= 10; i++) {
			const inputValue = parseFloat(o[`d${i}`]) || 0;
			total_off += inputValue;
			values[`d${i}`] = inputValue;
	}

	if( total_off > 100){
		frappe.msgprint('TPof cannot exceed 100%')
	}


	// TODO: PJOB Check the calculation
	o['tpof'] = total_off
	o['tnof'] = total_off/100 * (1 - o.dpl/100)*o.hna
	o['tpdisc'] = o.dpl + total_off*(1 - o.dpl/100)
	o['tndisc'] = (o['tpdisc']/100*o.hna).toFixed(0)

	// Update da1 to da10 with percentages

	for (let i = 1; i <= 10; i++) {
			const percentage = total_off === 0 ? 0 : (values[`d${i}`] / total_off) * 100;
			o[`a${i}`] = percentage
			let disc_real_off = ((1 - o.dpl/100) * values[`d${i}`]/100)
			let disc_onoff = (o.dpl/100) + disc_real_off
			o[`g${i}`] = disc_onoff * 100
			o[`p${i}`] = Math.round((disc_real_off) * o.hna)
	}


	frm.refresh_field('items');


	const over_hjm =
  o.tndisc > o.hjm_3 ? 3 :
  o.tndisc < o.hjm_3 && o.tndisc > o.hjm_2 && frm.doc.over_hjm < 2 ? 2 :
  o.tndisc < o.hjm_2 && o.tndisc > o.hjm_1 && frm.doc.over_hjm < 1 ? 1 : 0;

	frm.set_value("over_hjm", over_hjm);


	// if (o.tpdisc > o.hjm_3){
	// 	frm.set_value("over_hjm", 3)
	// } else if(o.tpdisc < o.hjm_3 && o.tpdisc > o.hjm_2 && frm.doc.over_hjm < 2){
	// 	frm.set_value("over_hjm", 2)
	// } else if(o.tpdisc < o.hjm_2 && o.tpdisc > o.hjm_1 && frm.doc.over_hjm < 1){
	// 	frm.set_value("over_hjm", 1)
	// } else frm.set_value("over_hjm", 0)

	try {
		paint_over_hjm(frm)
	}catch(error){
		console.log(error)
		try {
			paint_over_hjm_item(frm, o)
		}catch(error){console.log(error)}
	}


	frm.refresh_field(o.parentfield)
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

function set_parseXls_btn(frm){
	frm.add_custom_button(__('Get XLS'), function(){
		if(frm.doc.file){
			parseXLS(frm);
		} else {
			frappe.msgprint('Please upload the LPD File First')
		}
	});

	frm.add_custom_button(__('Download XLS'), function(){
			//download_template(frm)
			var method =
			'/api/method/bo.bo.doctype.lpd.lpd.download_template';

			var filters = [['name','=', frm.docname]];
			open_url_post(method, {
			doctype: frm.doctype,
			file_type: "Excel",
			export_fields: {"LPD":["name","outid","month","year","distributor","line","d1","d2","d3","d4","d5","d6","d7","d8","d9","d10","is_outlet_id"],"items":["name","item_code","item_name","hna","dpl","d1","d2","d3","d4","d5","d6","d7","d8","d9","d10"]},
			export_filters: filters,
			export_protect_area: [2, 22, 33],
		});
	});

}

function parseXLS(frm) {
	frm.call('parseXLS').then((res) => {
		console.log(res);
		if (res != undefined) {
			res = res.message;
			frm.doc.items = []
			frm.set_value("year", res.year);
			frm.set_value("month", res.month);
			frm.set_value("outid", res.outid);
			for (let i = 1; i <= 10; i++) {
				frm.set_value(`d${i}`, res.dx[i - 1]);
			}

			res.data.forEach((d) => {
				if (d[8] != null && d[1] in res.item_set) {
					frm.add_child('items', {
						'item_code': d[1],
						'item_name': d[2],
						'hna': d[3],
						'qty': d[5],
						'dpl': res.item_set[d[1]].disc, //[7]
						'd1': d[8],
						'd2': d[9],
						'd3': d[10],
						'd4': d[11],
						'd5': d[12],
						'd6': d[13],
						'd7': d[14],
						'd8': d[15],
						'd9': d[16],
						'd10': d[17],
						'hjm_1': d[33],
						'hjm_2': d[34],
						'hjm_3': d[35],
					});
				}
			}, frm, res);
			frm.doc.items.forEach((o) => {
				updatePercentages(frm, o);
			}, frm);
			frm.refresh_field('items');
		}
	});
}

function download_template(frm) {
	frappe.require('/assets/js/data_import_tools.min.js', () => {
		frm.data_exporter = new frappe.data_import.DataExporter(
			"LPD",
			"Insert New Records"
		);
	});
}


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


function paint_over_hjm(frm){
	frm.doc.items.forEach(o=>{
		if(frappe.user.has_role("SM") && o.tpdisc > o.hjm_1
		|| frappe.user.has_role("GSM") && o.tpdisc > o.hjm_2
		|| frappe.user.has_role("Accounts Manager") && o.tpdisc > o.hjm_1){
			cur_frm.fields_dict.items.grid.grid_rows[o.idx-1].row_index.css({"background-color":"#ffcccc"})
		} else{
			cur_frm.fields_dict.items.grid.grid_rows[o.idx-1].row_index.css({"background-color":"#fff"})
		}
	})
}

function paint_over_hjm_item(frm, o){
	if(frappe.user.has_role("SM") && o.tpdisc > o.hjm_1
	|| frappe.user.has_role("GSM") && o.tpdisc > o.hjm_2
	|| frappe.user.has_role("Accounts Manager") && o.tpdisc > o.hjm_1){
		frappe.ui.form.get_open_grid_form().grid_form.fields_dict.tpdisc.$input_wrapper.css({'color':'#f00'})
	} else{
		frappe.ui.form.get_open_grid_form().grid_form.fields_dict.tpdisc.$input_wrapper.css({'color':'#f00'}).css({'color':'#36414c'})
	}
}