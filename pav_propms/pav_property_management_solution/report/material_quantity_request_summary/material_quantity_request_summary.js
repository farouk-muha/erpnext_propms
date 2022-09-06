// Copyright (c) 2016, Patrner Team and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Material Quantity Request Summary"] = {
	"filters": [
	
		// {
		// 	fieldname: "from_date",
		// 	label: __("From Date"),
		// 	fieldtype: "Date",
		// 	reqd: 1,
		// 	"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		// },
		// {
		// 	fieldname: "to_date",
		// 	label: __("To Date"),
		// 	fieldtype: "Date",
		// 	reqd: 1,
		// 	"default": frappe.datetime.get_today()
		// },

		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},

		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "Link",
			options: "Cost Center",
		},

		{
			fieldname: "show_details",
			label: __("Show Details"),
			fieldtype: "Check",
		},
	]
};
