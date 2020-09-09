// Copyright (c) 2020, Sistem Koperasi and contributors
// For license information, please see license.txt

var username = frappe.session.user.replace(/@.*/g,"").toUpperCase()

frappe.ui.form.on('DPL', {
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
	   // frappe.db.get_value("Outlet", cur_frm.doc.outid,"territory").then((res)=>{
	   //     if(res.message.territory){
	   //         frm.set_value("territory", res.message.territory)
	   //     }
	   // })
	    
	},
	line: function(frm){
	    if(frm.doc.line == "")
	        return
		var items = frappe.db.get_list("Item", {filters:{"line":frm.doc.line},fields: ["item_code","item_name","standard_rate","ppg_item_code","ppg_item_name"], limit: 20})
		
		items.then((list)=>{
		    list.forEach((o,i)=>{
		        var ch = frm.add_child('items')
		        ch.item_code = o.item_code
				ch.item_name = o.item_name
				ch.ppg_item_code = o.ppg_item_code
				ch.ppg_item_name = o.ppg_item_name
		        ch.hna = o.standard_rate
		        ch.line = frm.doc.line
		    })
		    frm.refresh_field('items');
		})
	}
})

frappe.ui.form.on('DPL Item', {
	refresh(frm) {
		
	},
	item_code: function(frm) {
		
	}
})

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
