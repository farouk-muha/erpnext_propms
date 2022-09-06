// Copyright (c) 2021, Patrner Team and contributors
// For license information, please see license.txt


{% include 'erpnext/public/js/controllers/buying.js' %};
{% include 'erpnext/stock/doctype/material_request/material_request.js' %};


frappe.ui.form.on('Material Quantity Request', erpnext.buying.BuyingController.extend({
	
}));

frappe.ui.form.on("Material Quantity Request Item", {
	qty: function (frm, doctype, name) {
		var d = locals[doctype][name];
		if (flt(d.qty) < flt(d.min_order_qty)) {
			frappe.msgprint(__("Warning: Material Requested Qty is less than Minimum Order Qty"));
		}

		const item = locals[doctype][name];
		cur_frm.cscript.get_item_data(frm, item);
	},

	rate: function(frm, doctype, name) {
		const item = locals[doctype][name];
		cur_frm.cscript.get_item_data(frm, item);
	},

	item_code: function(frm, doctype, name) {
		const item = locals[doctype][name];
		item.rate = 0;
		cur_frm.cscript.get_item_data(frm, item);
	},
});

erpnext.buying.BuyingController.prototype.item_code = function(){
}
erpnext.buying.BuyingController.prototype.tc_name = function(){
}
erpnext.buying.BuyingController.prototype.validate_company_and_party = function(){
}
erpnext.buying.BuyingController.prototype.calculate_taxes_and_totals = function(){
}
erpnext.buying.BuyingController.prototype.validate = function(){
}
erpnext.buying.BuyingController.prototype.onload = function(){
}
erpnext.buying.BuyingController.prototype.items_add = function(){
}
erpnext.buying.BuyingController.prototype.items_add = function(){
}
erpnext.buying.BuyingController.prototype.items_add = function(){
}

$.extend(cur_frm.cscript, new erpnext.buying.BuyingController({frm: cur_frm}));




frappe.ui.form.on('Material Quantity Request', {
	refresh: function(frm){
		if(!frm.doc.total_amount || frm.doc.total_amount == 0){
			cur_frm.cscript.calculate_total(frm);
		}
	},
	
	setup:function(frm) {
		
		cur_frm.set_query("project_activities", "items" , function(doc, cdt, cdn) {
		var d = locals[cdt][cdn];
		return{
			filters: [
			
				['Project Activities', 'is_group', '=', 0],
			
			]
		}
		
		});    
		cur_frm.set_query("property", "items" ,  function(doc, cdt, cdn) {
		var d = locals[cdt][cdn];
		return{
			filters: [
				
				['Property', 'project', '=', d.project],
			]
		}
		});
		frm.custom_make_buttons = {
			'Stock Entry': 'Issue Material',
		};

		// formatter for material request item
		frm.set_indicator_formatter('item_code',
			function(doc) { return (doc.stock_qty<=doc.ordered_qty) ? "green" : "orange"; });

		frm.set_query("from_warehouse", "items", function(doc) {
			return {
				filters: {'company': doc.company}
			};
		});
	},
	project: function(frm, cdt, cdn) {
		if(!frm.doc.project) {
			erpnext.utils.copy_value_in_all_rows(frm.doc, cdt, cdn, "items", "project");
		}
	},
	cost_center: function(frm, cdt, cdn) {
		if(!frm.doc.cost_center) {
			erpnext.utils.copy_value_in_all_rows(frm.doc, cdt, cdn, "items", "cost_center");
		}
	},
	validate: function(frm){
		cur_frm.cscript.calculate_total(frm);
	},
})

cur_frm.cscript.get_item_data = function(frm, item) {
	if (item && !item.item_code) { return; }
	frm.call({
		method: "pav_propms.pav_property_management_solution.doctype.material_quantity_request.material_quantity_request.get_item_details",
		// method: "erpnext.stock.get_item_details.get_item_details",
		child: item,
		args: {
			args: {
				item_code: item.item_code,
				warehouse: "",
				doctype: frm.doc.doctype,
				buying_price_list: frappe.defaults.get_default('buying_price_list'),
				currency: frappe.defaults.get_default('Currency'),
				name: frm.doc.name,
				qty: item.qty || 1,
				stock_qty: item.stock_qty,
				company: frm.doc.company,
				conversion_rate: 1,
				material_request_type: frm.doc.material_request_type,
				plc_conversion_rate: 1,
				rate: item.rate,
				conversion_factor: item.conversion_factor
			}
		},
		callback: function(r) {
			const d = item;
			if(!r.exc) {
				$.each(r.message, function(k, v) {
					if(!d[k]) d[k] = v;
				});
			}
		}
	});
}

cur_frm.cscript.calculate_total = function(frm){
	var amount = 0;
	frm.doc.items.forEach(function(d){
		amount += d.amount;
	});
		
	frm.set_value('total_amount', amount || 0);
}