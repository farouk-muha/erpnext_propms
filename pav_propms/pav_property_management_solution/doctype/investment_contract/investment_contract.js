// Copyright (c) 2022, Patrner Team and contributors
// For license information, please see license.txt


frappe.ui.form.on('Investment Contract', {
	refresh: function (frm) {
		frm.set_query("supplier", function () {
			return {
				filters: {
					'investor': 1
				}
			};
		});
		frm.set_query("project_activities", function () {
			return {
				filters: {
					'is_group': 0
				}
			};
		});
	
		if(frm.doc.__onload && frm.doc.docstatus==1) {
			frm.set_df_property('create_payment', 'hidden', 0);	}else frm.set_df_property('create_payment', 'hidden', 1);
	},

	onload: function (frm) {
		if(frm.doc.amount)
		frm.set_value("account_currency", frm.doc.account_supplier.account_currency);
	},

	profit_percentage: (frm) => {
		if(frm.doc.amount)
		frm.set_value("profit_amount", frm.doc.amount * (frm.doc.profit_percentage / 100));
	},


	profit_amount: (frm) => {
		if(frm.doc.amount)
		frm.set_value("profit_percentage", (frm.doc.profit_amount * 100) / frm.doc.amount);
	},

	amount: (frm) => {
		
	
	if(frm.doc.amount){
		 frm.set_value("profit_percentage","");
		 frm.set_value("profit_amount", "");
		 frm.set_value("profit_percentage", "");
		 frm.set_value("investment_contract_template", "");
		 frm.set_value("investment_contract_term", "");}
	},
	supplier:(frm)=>{
		var doc =frm.doc;
			frappe.call({
				doc: doc,
				method: 'get_supplier_account',
				callback: function(r) {
					console.log(r.message)
					var i=0;
				}
			});
			cur_frm.add_fetch('account_supplier', 'account_currency', 'account_currency');

	}
,
	investment_contract_template: function (frm) {
		if (frm.doc.investment_contract_template) {

			frappe.call({
				method: 'pav_propms.pav_property_management_solution.doctype.investment_contract_template.investment_contract_template.get_contract_template',
				args: {
					template_name: frm.doc.investment_contract_template,
					doc: frm.doc
				},
				callback: function (r) {
					if (r && r.message) {
						frm.set_value("investment_contract_details", null);
						if (r.message.investment_contract_details) {
							r.message.investment_contract_details.forEach(element => {
								 	let d = frm.add_child("investment_contract_details");
								d.subject = element.subject;
								d.page_break = element.page_break;
							
							});
							frm.refresh_field("investment_contract_details");
						}
					}
				}
			});
		}
	},

	clear: function (frm) {
	frm.set_value("amount", null);
	frm.set_value("profit_amount", null);
	frm.set_value("profit_percentage", null);
	frm.set_value("investment_contract_template", null);
	frm.set_value("investment_contract_term", null);
	},

	investment_contract_type: function (frm) {
		if (frm.doc.investment_contract_type) {
			frm.set_value("investment_contract_term", null);
			frappe.call({
				doc: frm.doc,
				method: 'get_investment_contract_term',
				callback: function(r) {
					
					cur_frm.refresh_fields("investment_contract_term");
					
				}
			});
			
		}
	},


	
});

frappe.ui.form.on('Investment Contract Term', {
	// create_payment: function (frm,cdt,cdn){
	// 	let row = frappe.get_doc(cdt,cdn);
	// 	console.log(cur_frm.doc.supplier);
	// },
	
	create_payment: function (frm, cdt, cdn) {
		// if(frm.doc.__onload && frm.doc.docstatus==1) {
		if(frm.doc.docstatus==1) {

		var doc = frm.doc;
		let child = locals[cdt][cdn];
		console.log(child.name);
		frappe.call({
			method: "pav_propms.pav_property_management_solution.doctype.investment_contract.investment_contract.make_payment_entry",
			args: {
				doc: doc,
				child: child.name,
			},
			callback: function (r) {
				frappe.model.sync(r.message);
				// frappe.msgprint(r.message.party);
				frappe.set_route("Form", r.message.doctype, r.message.name);
			},
		});
	}
		// else frappe.msgprint("يجب ان يكون العقد معتمد");
	}






});






// supplier: function (frm) {
// 	if (frm.doc.supplier) {
// 		frappe.call({
// 			doc: frm.doc,
// 			method: "pav_propms.pav_property_management_solution.doctype.investment_contract.investment_contract.get_supplier_group",
// 			args: {
// 				doc: frm.doc,
// 				'supplier': frm.doc.supplier,
// 			},
// 			callback: function (r) {
// 				console.log("----",r)
// 			}
// 		});
// 	}
// },