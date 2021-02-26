// Copyright (c) 2020, Sistem Koperasi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dx Acc', {
	refresh(frm) {
		set_btns(frm)
		frm.set_intro('Please set Columns order to: ID, Number, RefNr, Note, Line');
	}
})

function set_btns(frm){

    frm.add_custom_button(__('Download XLS'), function(){
        var method =
				'/api/method/bo.bo.doctype.lpd.lpd.download_template';

        var filters = [['name','=', frm.docname]];
        open_url_post(method, {
			doctype: "Dx",
			file_type: "Excel",
			export_fields: {"Dx":["name"]},
// 			export_filters: filters,
			export_protect_area: [2, 3, 20],
		});
    });

    frm.add_custom_button(__('Read XLS'), function(){
        frm.call('parseXLS').then((res) => {
				console.log(res)
				if(res != undefined){
				    if(res.message.data){
				        var d = res.message.data
				        var columns = res.message.columns
				        console.log(d)
				        console.log(columns)
				        if(d.length > 0){
            				var str = '<table class="table" id="dxacc-records"><thead><tr>'
            				columns.forEach(e=>{
            				    str += '<td>' + e + '</td>'
            				})
            				str += '</tr><thead><tbody>'
            				var sum = 0
            				d.forEach(e => {
            				    str += '<tr>'
            				    e.forEach(f =>{
            				        str += '<td>'+f+'</td>'
            				    })
            					str += '</tr>'
            				});
            				str += '</tbody></table>'

        					frm.set_df_property('result', 'options', str);
                            frm.refresh_field('result');
                            $('#dxacc-records th,td').css({'border': '1px solid #d1d8dd'})

            				// $(".form-page").prepend(str)
            			} else{
            				$("#dppu-records").remove()
            			}
				    }
				}
			});
    });
}
