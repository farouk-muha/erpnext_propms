// Copyright (c) 2022, Farouk Muharram
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on('Purchase Order', {
    onload: function(frm) {
        frm.remove_custom_button('Material Request', "Get items from");
        frm.events.pav_make_custom_buttons(frm);
	},

	pav_make_custom_buttons: function(frm) {
		if (frm.doc.docstatus===0) {
			frm.add_custom_button(__('Material Request'), () => frm.events.get_items_from_material_request(frm),
				__("Get items from"));
		}
	},

    get_items_from_material_request: function(frm) {
        erpnext.utils.map_current_doc({
            method: "erpnext.stock.doctype.material_request.material_request.make_purchase_order",
			source_doctype: "Material Request",
			target: frm,
			setters: {
				title: undefined,
			},
			get_query_filters: {
				material_request_type: "Purchase",
                docstatus: 1,
                status: ["!=", "Stopped"],
                per_ordered: ["<", 99.99],
			}
		});
		
	},
	// project: function(frm){
	// 	frm.set_value('property', '');
	// },
    
})