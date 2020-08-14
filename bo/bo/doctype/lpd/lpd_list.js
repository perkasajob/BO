
frappe.listview_settings['LPD'] = {
	onload: function(listview){
		// let method = "frappe.email.inbox.create_email_flag_queue"
		// listview.page.add_menu_item(__("Mark as Read"), function() {
		// 	listview.call_for_selected_items(method, { action: "Read" });
		// });
	},
	refresh: function(listview) { 
		listview.page.add_action_item(__('Download XLS'), function(e,o){
			var method =
					'/api/method/bo.bo.doctype.dpl.dpl.download_template';
			var names = listview.get_checked_items().map((o,i)=>{
				return o.name
			})
			if (names.length > 0){				
				var export_filters = { "name": ["in", names]}				
				open_url_post(method, {
					doctype: listview.doctype,
					file_type: "Excel",
					export_fields: {[listview.doctype]:["name","outid","month","year","distributor","line","d1","d2","d3","d4","d5","d6","d7","d8","d9","d10","is_outlet_id"],"items":["name","item_code","item_name","hna","dpl_disc","d1","d2","d3","d4","d5","d6","d7","d8","d9","d10"]},
					export_filters: export_filters,
				});
			}
		});
		listview.page.add_action_item(__('Download XLS T'), function(e,o){
			var method =
					'/api/method/bo.bo.doctype.dpl.dpl.download_template';
			var names = listview.get_checked_items().map((o,i)=>{
				return o.name
			})
			if (names.length > 0){				
				var export_filters = { "name": ["in", names]}				
				open_url_post(method, {
					doctype: listview.doctype,
					file_type: "Excel",
					export_fields: {[listview.doctype]:["name","outid","month","year","distributor","line","d1","d2","d3","d4","d5","d6","d7","d8","d9","d10","is_outlet_id"],"items":["name","item_code","item_name","hna","dpl_disc","d1","d2","d3","d4","d5","d6","d7","d8","d9","d10","t1","t2","t3","t4","t5","t6","t7","t8","t9","t10"]},
					export_filters: export_filters,
				});
			}
		});
	}	
};
