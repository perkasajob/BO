frappe.listview_settings['DPF'] = {
	onload: function(listview){


	},
	refresh: function(listview) {
		listview.page.add_action_item("Refresh PO Status", () => {
			frappe.call({
						method: "bo.bo.doctype.dpl.dpl.refresh_po_status",
						callback: function(r) {
								if (!r.exc) {
										frappe.msgprint(__("{0}", [r]));
										// Optionally refresh the list
										listview.refresh();
								}
						}
				});
		}, "octicon octicon-plus");
	}
};
