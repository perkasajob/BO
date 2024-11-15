// Copyright (c) 2020, Sistem Koperasi and contributors
// For license information, please see license.txt

frappe.require("/assets/bo/js/bo-datatable.js")
$('<link/>', {
	rel: 'stylesheet',
	type: 'text/css',
	href: '/assets/bo/css/bo-datatable.css'
 }).appendTo('head');

const colReTotal = RegExp('^Sum of|^Total','gi');
var gdata = []
var gcolumns = []

frappe.ui.form.on('SLS', {
	onload: function(frm){
		if (!frappe.user.has_role("System Manager")) {
			$('.form-attachments').hide()
			$(".timeline-items").remove()
		}
	},
	onload_post_render: function(frm) {
		if(frm.doc.columns && frm.doc.data){
			var data = JSON.parse(frm.doc.data)
			var columns = JSON.parse(frm.doc.columns)
			columns[0] =  Object.assign(columns[0], {editable: false, format: formatFileName})
			columns.map(n=>{return n.name.match(colReTotal)? Object.assign(n, {width:120, editable: false, format: formatNumber}):n})
			var dataf=[]
			var found = false
			var re = new RegExp(loginName,"gi");

			data.every((d,i)=>{
				if(d.JABATAN.match(re, loginName)){
					dataf.push(d)
					found = true
				} else if(found){
					if(dataf[0].indent < d.indent){
						dataf.push(d)
					} else {return false}
				}
				return true
			})

			if (!frappe.user.has_role("System Manager") ) {
				data = dataf
			} else {
				frm.set_value({
					data: JSON.stringify(data),
					columns: JSON.stringify(columns)
				})
			}

			var datatable = new DataTable('.form-page', {
				columns: columns,
				data: data,
				treeView: true
			});

			cur_frm.datatable = datatable
			cur_frm.dt_data = data
			cur_frm.dt_columns = columns

		} else if($('.data-table').length > 0){
			location.reload();
		}
	},
	refresh: function(frm) {
		set_parseXls_btn(frm)

	}
});

function download_csv(fileName, urlData) {
	var aLink = document.createElement('a');
    aLink.download = fileName;
    aLink.href = urlData;

    var event = new MouseEvent('click');
    aLink.dispatchEvent(event);
}


function arrayToCSV(objArray) {
	const array = typeof objArray !== 'object' ? JSON.parse(objArray) : objArray;
	let str = `${Object.keys(array[0]).map(value => `"${value}"`).join(",")}` + '\r\n';

	return array.reduce((str, next) => {
		str += `${Object.values(next).map(value => `"${value}"`).join(",")}` + '\r\n';
		return str;
	   }, str);
}


function formatFileName(value, row, column, cell) {
	if (!row.meta.isLeaf) {
		return `<b>&nbsp;${value}</b>`;
	}

	return `<i class="fa fa-caret-right mr-2 text-muted"></i>&nbsp;${value}`;
}
function formatNumber(value, row, column, cell) {
	return format_number(value, null, 0);
}

var loginName = frappe.user.full_name()
function set_parseXls_btn(frm){
	frm.add_custom_button(__('Get CSV'), function(){
		download_csv(frm.doc.name+'.csv', 'data:text/csv;charset=UTF-8,' + encodeURIComponent(Papa.unparse(cur_frm.dt_data)))
	})

    frm.add_custom_button(__('Read XLS'), function(){
		// $.when(
		// 	$.getScript( "/assets/bo/js/bo-datatable.js" ),
		// 	$.Deferred(function( deferred ){
		// 		$( deferred.resolve );
		// 	})
		// ).done(function( script, textStatus ) {
		frm.call('parseXLS').then((res) => {
			debugger
			if(res != undefined){
				if(res.message.data){
					var data = []
					let nrow_column = 2 //starting row number as header
					let total_col_nr = 0
					// const colReTotal = RegExp('^Sum of|^Total','gi');
					total_col_nr = res.message.data[nrow_column].findIndex((d, idx)=>{return colReTotal.test(d)})

					var columns = [{name: 'JABATAN', width:400, editable: false, format: formatFileName}].concat(res.message.data[nrow_column].slice(5).map(n=>{return n.match(colReTotal)?{name: n, width:120, editable: false, format: formatNumber}:{name: n, width:150}}))

					res.message.data.forEach((dat,i)=>{
						let isbreak = false
						let isExtraRow = true
						if(i > nrow_column){
							dat.forEach((c, j)=>{
								if(j < 5){
									if(c){
										if(c !== "Grand Total"){
											if( c.substr(-5) === "Total"){
												let rowIdx = data.findIndex((d, idx)=>{return d.JABATAN==c.substr(0, c.length-6)})
												// data[rowIdx][frm.doc.header_value] = dat[total_col_nr]
												var tc = totalCols(dat, res.message.data[nrow_column], total_col_nr)
												Object.keys(tc).forEach(k=>{data[rowIdx][k] = tc[k]})
												isbreak = true
											} else {
												// data.push({'JABATAN': c, 'indent': j, [frm.doc.header_value]:dat[total_col_nr]});
												let ec = extraCols(dat, columns, j)
												if(j == 4){
													data.push(Object.assign({'JABATAN': c, 'indent': j}, {}));
													data.push(Object.assign({'JABATAN': '-', 'indent': 5}, ec));
												} else
													data.push(Object.assign({'JABATAN': c, 'indent': j}, ec));
											}
										}
										isExtraRow = false
									} else { isbreak = true}
								} else if(c && !isbreak){
									data[data.length-1][res.message.data[nrow_column][j]] = c
								}
							})
							if(isExtraRow){
								let ec = extraCols(dat, columns, 4, total_col_nr)
								data.push(Object.assign({'JABATAN': '-', 'indent': 5}, ec));
							}
						}
					})
					var dataf=[]
					var found = false
					var re = new RegExp(loginName,"gi");
					data.every((d,i)=>{
						if(d.JABATAN.match(re, loginName)){
							dataf.push(d)
							found = true
						} else if(found){
							if(dataf[0].indent < d.indent){
								dataf.push(d)
							} else {return false}
						}
						return true
					})

					if (!frappe.user.has_role("System Manager") ) {
						data = dataf
					} else {
						frm.set_value({
							data: JSON.stringify(data),
							columns: JSON.stringify(columns)
						})
					}
					gdata = data
					gcolumns = columns

					let datatable = new DataTable('.form-page', {
						columns: columns,
						data: data,
						treeView: true
					});
				}
			}
		});
	});
}

function totalCols(dat, columns,total_col_nr){
	let el = {}
	let j = 0
	for(var i=total_col_nr;i<dat.length;i++){
		j++;
		el[columns[i]] = dat[i]
	}
	return el
}

function extraCols(dat, columns, j){
	let el = {}
	let k = 0
	let isLeaf = j==4

	for(var i=5;i<dat.length;i++){
		k++;
		el[columns[k].name] = isLeaf?dat[i]: null
	}
	return el
}

var groupBy = function(data, key) { // `data` is an array of objects, `key` is the key (or property accessor) to group by
  // reduce runs this anonymous function on each element of `data` (the `item` parameter,
  // returning the `storage` parameter at the end
  return data.reduce(function(storage, item) {
    // get the first instance of the key by which we're grouping
    var group = item[key];

    // set `storage` for this instance of group to the outer scope (if not empty) or initialize it
    storage[group] = storage[group] || [];

	// add this item to its group within `storage`
	console.log(item)
    storage[group].push(item);

    // return the updated storage to the reduce function, which will then loop through the next
    return storage;
  }, {}); // {} is the initial value of the storage
};

// const groupBy = (data, keys) => { // `data` is an array of objects, `keys` is the array of keys (or property accessor) to group by
//   // reduce runs this anonymous function on each element of `data` (the `item` parameter,
//   // returning the `storage` parameter at the end
//   return data.reduce((storage, item) => {
//     // returns an object containing keys and values of each item
//     const groupValues = keys.reduce((values, key) => {
//       values[key] = item[key];
//       return values;
//     }, {});

//     // get the first instance of the key by which we're grouping
//     const group = Object.values(groupValues).join(' ');

//     // set `storage` for this instance of group to the outer scope (if not empty) or initialize it
//     storage[group] = storage[group] || [];

//     // add this item to its group within `storage`
//     if (keys.every((key) => item[key] === groupValues[key])) {
//       storage[group].push(item);
//     }

//     // return the updated storage to the reduce function, which will then loop through the next
//     return storage;
//   }, {}); // {} is the initial value of the storage
// };

function download_template(frm) {
		frappe.require('/assets/js/data_import_tools.min.js', () => {
			frm.data_exporter = new frappe.data_import.DataExporter(
				"DPL",
				"Insert New Records"
			);
		});
	}