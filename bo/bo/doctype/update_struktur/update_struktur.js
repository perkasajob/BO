// Copyright (c) 2023, Sistem Koperasi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Update Struktur', {
	setup(frm) {
		frappe.realtime.on('update_struktur_refresh', ({ data_import }) => {
			frm.import_in_progress = false;
			if (data_import !== frm.doc.name) return;
			frappe.model.clear_doc('Data Import', frm.doc.name);
			frappe.model.with_doc('Data Import', frm.doc.name).then(() => {
				frm.refresh();
			});
		});
		frappe.realtime.on('update_struktur_progress', data => {
			frm.import_in_progress = true;
			console.log(data)
			let percent = Math.floor((data.current * 100) / data.total);
			let seconds = Math.floor(data.eta);
			let minutes = Math.floor(data.eta / 60);
			let eta_message =
				// prettier-ignore
				seconds < 60
					? __('About {0} seconds remaining', [seconds])
					: minutes === 1
						? __('About {0} minute remaining', [minutes])
						: __('About {0} minutes remaining', [minutes]);

			let message;
			if (data.success) {
				let message_args = [data.level, data.current, data.total, eta_message, data.docname];
				message =
					frm.doc.import_type === 'Insert New Records'
						? __('Importing {0}: {1} of {2}, {3}, {4}', message_args)
						: __('Updating {0}: {1} of {2}, {3}, {4}', message_args);
			}
			if (data.skipping) {
				message = __('Skipping {0} of {1}, {2}', [
					data.current,
					data.total,
					eta_message
				]);
			}
			frm.dashboard.show_progress(__('Import Progress'), percent, message);
			frm.page.set_indicator(__('In Progress'), 'orange');

			// hide progress when complete
			if (data.current === data.total) {
				setTimeout(() => {
					frm.dashboard.hide();
					frm.refresh();
				}, 2000);
			}
		});
	},
	refresh(frm) {
		set_btns(frm)
		frm.set_intro('Columns: GSMID, GSMNAME, SMID, SMNAME, AMID, AMNAME, DMID, DMNAME, SPVID, SPVNAME, TPID, TPNAME, divid, desc, area, TSJ ORG CODE');
	}
});
function set_btns(frm){
	frm.add_custom_button(__('Read XLS'), function(){
		frm.call('parseXLS').then((res) => {
				if(res != undefined){
					if(res.message.data){
						var d = res.message.data
						var columns = res.message.columns
						console.log("Starting .....")
						// console.log(columns)
						// debugger
						// if(d.length > 0){
						// 	var str = '<table class="table" id="struktur"><thead><tr>'
						// 	columns.forEach(e=>{
						// 		str += '<td>' + e + '</td>'
						// 	})
						// 	str += '</tr><thead><tbody>'
						// 	var sum = 0
						// 	d.forEach(e => {
						// 		str += '<tr>'
						// 		e.forEach(f =>{
						// 			str += '<td>'+f+'</td>'
						// 		})
						// 		str += '</tr>'
						// 	});
						// 	str += '</tbody></table>'

						// 	frm.set_df_property('data', 'options', str);
						// 	frm.refresh_field('data');
						// 	$('#struktur th,td').css({'border': '1px solid #d1d8dd'})

						// 	// $(".form-page").prepend(str)
						// } else{
						// 	$("#struktur").remove()
						// }
					}
				}
			});
	});
}