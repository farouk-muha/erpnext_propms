// Copyright (c) 2022, Farouk Muharram
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on('Purchase Invoice', {
	refresh: function(frm){

		if (frm.doc.docstatus == 1 && frm.doc.has_letter_of_guarantee && !frm.doc.guarantee_jv && 
			frm.doc.guarantee_account && frm.doc.guarantee_percent > 0) {
			frm.add_custom_button(__('Create JV Guarantee'), function() {
				frappe.call({
					method: "pav.pav.utils.make_jv_entry_for_guarantee_from_purchase_invoice",
					args: {
						dt: frm.doc.doctype,
						dn: frm.doc.name,
					},
					callback: function (r) {
						if (r) {
							frappe.set_route("Form", "Journal Entry", r.message.name);
						}
					}
				})
			}, __("Guarantee"));
			}
		if (frm.doc.docstatus==1 && frm.doc.guarantee_jv) {
			frm.add_custom_button(__('Cancel JV Guarantee'), function() {
				frappe.call({
					method: "pav.pav.utils.cancel_jv_entry_for_guarantee_from_purchase_invoice",
					args: {
						dt: frm.doc.doctype,
						dn: frm.doc.name,
					},
					callback: function (r) {
						
							frm.refresh()
						
					}
				})
			}, __("Guarantee"));

			// frm.add_custom_button(__('PAV Payment Request'), () => frm.events.create_payment_request(frm, 'Guarantee'), __("Guarantee"));
		}
	},
	pav_make_custom_buttons: function(frm) {

		if (frm.doc.docstatus===1) {
			frm.add_custom_button(__('PAV Payment Request'), () => frm.events.create_payment_request(frm),
				__("Create"));
		}
		
		// if (frm.doc.docstatus===0) {
		// 	frm.add_custom_button(__('Purchase Order'), () => frm.events.get_items_from_material_request(frm),
		// 		__("Get items from"));
		// }
	},
	create_payment_request: function(frm, type = "Purchase Invoice"){
		frappe.model.open_mapped_doc({
	        method: "pav.pav.doctype.pav_payment_request.pav_payment_request.create_payment_request",
    		frm: frm,
    		args: {'type': type},
    	})
	},
    get_items_from_material_request: function(frm) {
        erpnext.utils.map_current_doc({
			method: "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_invoice",
			source_doctype: "Purchase Order",
			target: frm,
			setters: {
				title: undefined,
			},
			get_query_filters: {
				docstatus: 1,
				status: ["not in", ["Closed", "On Hold"]],
				per_billed: ["<", 99.99],
				company: me.frm.doc.company
			}
		});
		
	},
	validate: function(frm){
		if(frm.doc.currency != erpnext.get_currency(frm.doc.company) && (frm.doc.conversion_rate == 1)){
			frappe.msgprint(__("Exchange Rate cant be 1"));
            frappe.validated = false;
		}
	},
	project: function(frm){
		frm.set_value('property', '');
	},

})