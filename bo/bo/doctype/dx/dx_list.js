frappe.listview_settings['Dx'] = {	
	onload: function(listview){		
		if((frappe.user.has_role("DM") || frappe.user.has_role("SM") || frappe.user.has_role("GSM")) && !frappe.user.has_role("Administrator")){
			$(".page-form").hide()
			$(".filter-list").hide()
			
			throw("not allowed!")
			// frappe.db.get_value('DM', {'dm_name':frappe.user.name}, 'territory').then((r)=>{
			// 	if(r.message.territory){
			// 		if (!frappe.route_options){ //remove this condition if not required
			// 			frappe.set_route("List", "Dx", {"territory": r.message.territory});
			// 		}
			// 	}
			// })			
		}
	},
	refresh: function(listview) { 
		
	}	
};