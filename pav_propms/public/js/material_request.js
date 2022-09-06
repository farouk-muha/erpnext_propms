// Copyright (c) 2022, Farouk Muharram
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on('Material Request', {
	onload: function(frm) {
        frm.remove_custom_button('Product Bundle', "Get items from");
       
	},
    refresh: function(frm) {
		frm.remove_custom_button('Purchase Order', "Create");
        frm.events.pav_make_custom_buttons(frm);

		if(!frm.doc.total_amount || frm.doc.total_amount == 0)
			frm.events.calculate_total(frm);
	},

	pav_make_custom_buttons: function(frm) {
		if (frm.doc.docstatus===0) {
			frm.add_custom_button(__('Material Quantity Request'), () => frm.events.get_items_from_material_quantity_request(frm),
				__("Get items from"));

				frm.remove_custom_button('Sales Order', "Get items from");
				frm.remove_custom_button('Bill of Materials', "Get items from");
				// frm.remove_custom_button('Product Bundle', "Get items from");
		}

		if (frm.doc.material_request_type === "Purchase") {
			frm.add_custom_button(__('Purchase Order'),
				() => frm.events.make_purchase_order(frm), __('Create'));
		}
	},

    get_items_from_material_quantity_request: function(frm) {
        erpnext.utils.map_current_doc({
			method: "pav_propms.pav_property_management_solution.doctype.material_quantity_request.material_quantity_request.make_material_quantity_request",
			source_doctype: "Material Quantity Request",
			target: frm,
			setters: {
				title: "",
			},
			get_query_filters: {
				docstatus: 1,
			}
		});
		
	},

	make_purchase_order: function(frm) {
		frappe.prompt(
			{
				label: __('For Default Supplier (Optional)'),
				fieldname:'default_supplier',
				fieldtype: 'Link',
				options: 'Supplier',
			},
			(values) => {
				frappe.model.open_mapped_doc({
					method: "erpnext.stock.doctype.material_request.material_request.make_purchase_order",
					frm: frm,
					args: { default_supplier: values.default_supplier },
					run_link_triggers: true
				});
			},
			__('Enter Supplier')
		)
	},
    validate: function(frm){
		frm.events.calculate_total(frm);
	},
	calculate_total: function(frm){
		var amount = 0;
		frm.doc.items.forEach(function(d){
			amount += d.amount;
		});			
		frm.set_value('total_amount', amount || 0);
	}
})

