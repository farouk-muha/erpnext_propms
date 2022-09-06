// Copyright (c) 2018, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Property', {
	refresh: function(frm) {
		frm.set_query('cost_center', () => {
			return {
				filters: {
					is_group: 0
					}
				};
			});
			frm.set_query('quotation', () => {
			return {
				filters: {
					property: frm.doc.name
					}
				};
			});
			frm.set_query('sales_order', () => {
			return {
				filters: {
					property: frm.doc.name
					}
				};
			});
			frm.set_query('contract', () => {
			return {
				filters: {
					property: frm.doc.name
					}
				};
			});
			frm.set_query('delivery_note', () => {
			return {
				filters: {
					property: frm.doc.name
					}
				};
			});

			cur_frm.set_query("sales_invoice", function(doc, cdt, cdn) {
				var d = locals[cdt][cdn];
				return{
					filters: [
						
						['Sales Invoice', 'project', '=', d.project],
			
					]
				}
				});

				cur_frm.set_query("parent_property", function(doc, cdt, cdn) {
					var d = locals[cdt][cdn];
					return{
						filters: [
							
							['Property', 'project', '=', d.project],
							['Property', 'is_group', '=', 1],
				
						]
					}
					});
	},
	setup: function(frm) {

	},

	status: function(frm) {		
		cur_frm.set_value("quotation", '');
		cur_frm.set_value("sales_order", '');
		cur_frm.set_value("sales_invoice", '');
		cur_frm.set_value("contract", '');
		cur_frm.set_value("delivery_note", '');
		cur_frm.set_value("customer", '');
		console.log(frm.doc.status);

		if(frm.doc.status == 'Booked'){
			console.log('Booked');
			frm.set_df_property('quotation', 'reqd', 1);
			frm.set_df_property('sales_order', 'reqd', 0);
			frm.set_df_property('contract', 'reqd', 0);
			frm.set_df_property('delivery_note', 'reqd', 0);

		}else if(frm.doc.status == 'Initial Contract'){
			frm.set_df_property('quotation', 'reqd', 0);
			frm.set_df_property('sales_order', 'reqd', 1);
			frm.set_df_property('contract', 'reqd', 0);
			frm.set_df_property('delivery_note', 'reqd', 0);

		}else if(frm.doc.status == 'Final Contract'){
			frm.set_df_property('quotation', 'reqd', 0);
			frm.set_df_property('sales_order', 'reqd', 0);
			frm.set_df_property('contract', 'reqd', 1);
			frm.set_df_property('delivery_note', 'reqd', 0);

		}else if(frm.doc.status == 'Deivery Note'){
			frm.set_df_property('quotation', 'reqd', 0);
			frm.set_df_property('sales_order', 'reqd', 0);
			frm.set_df_property('contract', 'reqd', 0);
			frm.set_df_property('delivery_note', 'reqd', 1);

		}		
	},
	get_customr: function(frm, doctype, filter, fieldname){
		if (!filter)
		return;
		
		frappe.call({
			"method": "frappe.client.get_value",
			"args": {
				"doctype": doctype,
				"filters": filter,
				"fieldname": fieldname
			},
			freeze:true,
			"callback": function(res){

				if (!res.exc){
				cur_frm.set_value("customer", res.message[fieldname]);
				}
			}
		});
	},
	quotation: function(frm) {
		frm.events.get_customr(frm, 'Quotation', frm.doc.quotation, 'party_name');
	},

	sales_order: function(frm) {
		frm.events.get_customr(frm, 'Sales Order', frm.doc.sales_order, 'customer');
	},
	
	sales_invoice: function(frm) {
		frm.events.get_customr(frm, 'Sales Invoice', frm.doc.sales_invoice, 'customer');
	},

	apartment_space:function(frm) {
	    var price = (flt(frm.doc.apartment_space) * flt(frm.doc.price_per_cube_meter));
	    frm.set_value("apartment_price", price);
	},
	
	price_per_cube_meter:function(frm) {
	    var price = (flt(frm.doc.apartment_space) * flt(frm.doc.price_per_cube_meter));
	    frm.set_value("apartment_price", price);
	},
	
	amount_paid:function(frm) {
	    var amount_paid = (frm.doc.apartment_price) - (frm.doc.amount_paid);
	    frm.set_value("remaining_amount", amount_paid);
	},
	
	property_type:function(frm) {
		if(["مجمع سكني","برج سكني","ادوار"].includes(frm.doc.property_type)){
	        frm.set_value("is_group", 1);
	        frm.set_df_property("is_group", "read_only", 1);
	    }else{
	     frm.set_value("is_group", 0);
	     frm.set_df_property("is_group", "read_only", 0);
	    }
	    if(frm.doc.property_type == "شقة"){
	        frm.set_df_property("apartment_space", "reqd", 1);
	        frm.set_df_property("price_per_cube_meter", "reqd", 1);
	        frm.set_df_property("is_group", "read_only", 1);
	    }else{
	        frm.set_df_property("apartment_price", "reqd", 0);
	    }
	},
});


