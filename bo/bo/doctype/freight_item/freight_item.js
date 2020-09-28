// Copyright (c) 2020, Sistem Koperasi and contributors
// For license information, please see license.txt

var priceList = []
frappe.ui.form.on('Freight Item', {
	refresh(frm) {
		set_btns(frm)
	}
})

function set_btns(frm){
    var priceList = eval(tsvJSON(cur_frm.doc.data))
	priceList.map(o=>{return parseD(o)})
    frm.add_custom_button(__('Freight Cost'), function(){
        let freight = 'D1'
        if(frm.doc.qty > 1200){
            frappe.msgprint("Please Enter Quantity below 1200", "Max capacity exceeded")
            return
        }else if(frm.doc.qty <= 1200 && frm.doc.qty >= 600){
            freight = 'D1'
        }else if(frm.doc.qty < 600 && frm.doc.qty >= 300){
            freight = 'D2'
        }else if(frm.doc.qty > 0 && frm.doc.qty < 300){
            freight = 'D3'
        }
        var x = priceList.filter(o=>{return o.Destination == frm.doc.destination})
        let price = x[0][freight]/parseInt(frm.doc.qty)
        frappe.msgprint("<p>Quantity: " + frm.doc.qty +' Box</p>Rent : '+ currencyFormat(x[0][freight]) +'</p><p>Rent/Box : ' + currencyFormat(price)+'</p>' , "Freight to " + frm.doc.destination);
    })
};


function parseD(o){
    o.D1 = parseInt(o.D1.trim().replace(/\,/gi, ''))
    o.D2 = parseInt(o.D2.trim().replace(/\,/gi, ''))
    o.D3 = parseInt(o.D3.trim().replace(/\,/gi, ''))
    return o
}

function currencyFormat(num) {
  return 'Rp. ' + num.toFixed(2).replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,')
}

function tsvJSON(tsv){
 
  var lines=tsv.split("\n");
 
  var result = [];
 
  var headers=lines[0].split("\t");
 
  for(var i=1;i<lines.length;i++){
	  var obj = {};
	  var currentline=lines[i].split("\t");
 
	  for(var j=0;j<headers.length;j++){
		  obj[headers[j]] = currentline[j];
	  }
	  result.push(obj);
  }
  return JSON.stringify(result);
}
