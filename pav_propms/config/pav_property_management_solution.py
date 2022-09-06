# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _

def get_data():
	config = [
		{
			"label": _("PAV Property Management Solution"),
			"items": [
				{
					"type": "doctype",
					"name": "Property",
					"description": _("Property that needs to be managed."),
				},
				{
					"type": "doctype",
					"name": "Rent Request",
				},
				{
					"type": "doctype",
					"name": "Rent Contract",
				},
				{
					"type": "doctype",
					"name": "Tenant Add",
				},
				{
					"type": "doctype",
					"name": "Property Delivery Order",
				},
                {
					"type": "doctype",
					"name": "Rent Warning",
				},	
                {
					"type": "doctype",
					"name": "Property Evacuate",
				},
                {
					"type": "doctype",
					"name": "Receipt Note",
				},
                {
					"type": "doctype",
					"name": "Property Assets",
				},
                {
					"type": "doctype",
					"name": "Property Contents",
				},
				{
					"type": "doctype",
					"name": "Material Quantity Request",
				},	
				{
					"type": "doctype",
					"name": "Real Estate Settings",
				},
			]
		},
		{
			"label": _("Services"),
			"icon": "fa fa-cog",
			"items": [
				{
					"type": "doctype",
					"name": "Assigning Maintenance",
				},
				{
					"type": "doctype",
					"name": "Electricity Invoice",
				},
				{
					"type": "doctype",
					"name": "Residents Complaints",
				},
				{
					"type": "doctype",
					"name": "Technical Services Report",
				},				
			]
		},
		{
			"label": _("Property Settings"),
			"items": [
				{
					"type": "doctype",
					"name": "Meter Readings",
				},
                {
					"type": "doctype",
					"name": "Meter Readings",
				},
			]
		},
		{
			"label": _("Reports"),
			"items": [
				{
					"type": "report",
					"name": "Property Status",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Accounting Dimension Balance Pro",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Accounting Dimension Bill Of Quantity",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Purchase Order Summary",
					"is_query_report": True
				},
			]
		}
	]
	return config
