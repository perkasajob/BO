frappe.listview_settings['Mkt'] = {
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
					export_fields: {[listview.doctype]:["name","date","dx","territory","sm","dm","mr","number","dppu","ref_nr","note","line"]},
					export_filters: export_filters,
					// export_protect_area: [],
				});
			}
		});
	}
}