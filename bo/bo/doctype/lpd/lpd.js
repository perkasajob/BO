// Copyright (c) 2020, Quantum Labs and contributors
// For license information, please see license.txt

var username = frappe.session.user.replace(/@.*/g,"").toUpperCase()

frappe.ui.form.on('LPD', {
    onload: function(frm){
        if(frappe.user.has_role("DM")){
            frappe.db.get_value("DM","DM-"+username,"territory",function(res){
              if(res != undefined){
                frm.set_value("territory", res.territory)
                set_filter_by_territory(frm, res.territory)
              } 
            })
        }
    },
	refresh: function(frm) {
	    set_parseXls_btn(frm)
	},
	year: function(frm){
	    //frm.set_value("start_date",moment(frm.doc.start_date).startOf("month"))
	    frm.set_value("month_code", frm.doc.year.substring(2) + frm.doc.month)
	},
	month: function(frm){
	    frm.set_value("month_code", frm.doc.year.substring(2) + frm.doc.month)
	},
	outid: function(frm){
	    frm.set_value("outlet_name", frm.doc.outid.replace(/^.*-/g,""))
	    frm.set_value("is_outlet_id", frm.doc.outid.match(/^[0-9_]+/g)[0])
	    
	},
	start_date: function(frm){
	    //frm.set_value("start_date",moment(frm.doc.start_date).startOf("month"))
	    //frm.set_value("end_date",moment(frm.doc.start_date).endOf("month"))
	    //frm.set_value("month",moment(frm.doc.start_date).startOf("month").format("MMYY"))
	    //frm.set_value("start_date",frm.doc.start_date.replace(/^\d+-/g,"01-"))
	    
	},
	line: function(frm){
	    if(frm.doc.line == "")
	        return
		var items = frappe.db.get_list("Item", {filters:{"line":frm.doc.line},fields: ["item_code","item_name","standard_rate"], limit: 20})
		
		items.then((list)=>{
		    list.forEach((o,i)=>{
		        var ch = frm.add_child('items')
		        ch.item_code = o.item_code
		        ch.item_name = o.item_name
		        ch.hna = o.standard_rate
		        ch.line = frm.doc.line
		    })
		    frm.refresh_field('items');
		})
	}
})

frappe.ui.form.on('LPD Item', {
	refresh(frm) {
		
	},
	item_code: function(frm) {
		
	}
})
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
        
        frm.call('parseXLS').then((res) => {
				console.log(res)
				if(res != undefined){
				    if(res.message.data){
				        frm.doc.items.splice(frm.doc.items[0])
				        for(let i = 0; i < res.message.data.length; i++){
				            var dat = res.message.data[i]
				            var startEl = 22
				            var rowNotEmpty = dat.slice(startEl).find(el=>el>0)
				            if(rowNotEmpty){
    				            var ch = frm.add_child('items')
                		        ch.item_code = dat[18]
                		        ch.item_name = dat[19]
                		        ch.hna = dat[20]
                		        ch.dpl_disc = dat[21]
                		        ch.d1 = dat[22]
                		        ch.d2 = dat[23]
                		        ch.d3 = dat[24]
                		        ch.d4 = dat[25]
                		        ch.d5 = dat[26]
                		        ch.d6 = dat[27]
                		        ch.d7 = dat[28]
                		        ch.d8 = dat[29]
                		        ch.d9 = dat[30]
                		        ch.d10 = dat[31]
                		        ch.line = frm.doc.line
				            }
				        }
				        frm.refresh_field('items')
				    }
				}
			});
    });
    frm.add_custom_button(__('Download XLS'), function(){
        //download_template(frm)
        var method =
				'/api/method/bo.bo.doctype.lpd.lpd.download_template';

        var filters = [['name','=', frm.docname]];
        open_url_post(method, {
			doctype: frm.doctype,
			file_type: "Excel",
			export_fields: {"LPD":["name","outid","month","year","distributor","line","d1","d2","d3","d4","d5","d6","d7","d8","d9","d10","is_outlet_id"],"items":["name","item_code","item_name","hna","dpl_disc","d1","d2","d3","d4","d5","d6","d7","d8","d9","d10"]},
			export_filters: filters,
			export_protect_area: [2, 22, 33],
		});
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
