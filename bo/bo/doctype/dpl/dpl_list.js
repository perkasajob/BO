frappe.listview_settings['DPL'] = {
	onload: function(listview){
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
					export_fields: {[listview.doctype]:["name","outid","month","year","distributor","line","is_outlet_id"],"items":["name","item_code","item_name","hna","dpl_disc"]},
					export_filters: export_filters,
					export_protect_area: [2, 11, 12],
				});
			}
		});

		listview.page.add_action_item(__('Dwnld Distro XLS'), function(e,o){
			var method = '/api/method/bo.bo.doctype.dpl.dpl.download_template';
			var names = listview.get_checked_items().map((o,i)=>{
				return o.name
			})
			if (names.length > 0){
				var export_filters = { "name": ["in", names]}
				open_url_post(method, {
					doctype: listview.doctype,
					file_type: "Excel",
					export_fields: {[listview.doctype]:["name","outid", "start_date", "end_date", "distributor","line","is_outlet_id","apl_outid","ppg_outid","tsj_outid"],"items":["name","item_code","item_name","hna","dpl_disc","hna1","dpl_disc1","nsv1_ppn","apl_item_code","apl_item_name","ppg_item_code","ppg_item_name","tsj_item_code","tsj_item_name"]},
					export_filters: export_filters,
					export_protect_area: [2, 12, 13],
				});
			}
		});
	}
};
