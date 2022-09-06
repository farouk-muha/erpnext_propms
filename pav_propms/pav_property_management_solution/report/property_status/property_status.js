// Copyright (c) 2016, Patrner Team and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Property Status"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 1,
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 1,
			"default": frappe.datetime.get_today()
		},
		{
			fieldname: "status",
			label: __("Stauts"),
			fieldtype: "Select",
			options:['', 'Available', 'Booked', 'Initial Contract', 'Final Contract', 'Delivery Note'],
			default:'Available'
		},
		{
			fieldname: "property",
			label: __("Property"),
			fieldtype: "Link",
			options: "Property",
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "property_type",
			label: __('Property Type'),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return frappe.db.get_link_options("Property Type", txt);
			}
		},
		{
			fieldname: "account",
			label: __('Account'),
			fieldtype: "Link",
			options: "Account",
		},
		{
			fieldname: "temporary_booked",
			label: __('Temporary Booked'),
			fieldtype: "Select",
			options: ["", {"label": __("Yes"), "value": 1}, {"label": __("No"), "value": 0}],
		},
		{
			fieldname: "show_details",
			label: __("Show Details"),
			fieldtype: "Check",
		},
	],
};

