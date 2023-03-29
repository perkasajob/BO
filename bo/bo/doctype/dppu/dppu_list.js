frappe.listview_settings['DPPU'] = {
	colwidths: {"subject": 1},
	add_fields: ["status"],
	onload: function(listview){
		// let method = "frappe.email.inbox.create_email_flag_queue"
		// listview.page.add_menu_item(__("Mark as Read"), function() {
		// 	listview.call_for_selected_items(method, { action: "Read" });
		// });

		if (!frappe.route_options){ //remove this condition if not required
			frappe.route_options = {
				"session_type": ["=", "Individual"]
			};
		}
	},
	refresh: function(listview) {
		if(!frappe.user.has_role("DM") && !frappe.user.has_role("SM") && !frappe.user.has_role("GSM")){
			listview.page.add_menu_item(__('Download XLS'), function(e,o){
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
						export_fields: {[listview.doctype]:["name","workflow_state","blanko_nr","dm_user", "dm", "dm_area", "approver_1", "approver_1_name", "approver_2", "approver_2_name", "mss", "mss_name", "tp", "tp_name", "kota", "territory","mr_user", "dx_user", "saldo", "cash_transfer","number","date","comment","jml_ccln", "jv_type", "jv_date", "jv_in", "jv_out", "note", "dm_v", "tp_v", "extra_v", "approver_1_v"]},
						export_filters: export_filters,
						export_protect_area: [2, 10, 11],
					});
				}
			});
		}
	}
};
