# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import json

import frappe
from frappe import _, throw
from frappe.utils import add_days, cstr, date_diff, get_link_to_form, getdate
from frappe.utils.nestedset import NestedSet
from frappe.desk.form.assign_to import close_all_assignments, clear
from frappe.utils import date_diff

class CircularReferenceError(frappe.ValidationError): pass
class EndDateCannotBeGreaterThanProjectEndDateError(frappe.ValidationError): pass

class Property(NestedSet):
	nsm_parent_field = 'parent_property'


 
@frappe.whitelist()
def get_children(doctype, parent, property=None, project=None, is_root=False):

	filters = [['docstatus', '<', '2']]

	if property:
		filters.append(['parent_property', '=', property])
	elif parent and not is_root:
		# via expand child
		filters.append(['parent_property', '=', parent])
	else:
		filters.append(['ifnull(`parent_property`, "")', '=', ''])

	if project:
		filters.append(['project', '=', project])

	activities = frappe.get_list(doctype, fields=[
		'name as value',
		'property_code as title',
		'is_group as expandable'
	], filters=filters, order_by='name')

	# return activities
	return activities

@frappe.whitelist()
def add_node():
	from frappe.desk.treeview import make_tree_args
	args = frappe.form_dict

	args = make_tree_args(**args)

	if args.parent_property == 'All Property' or args.parent_property == args.project:
		args.parent_property = None
		
	if args.parent_property != None:
		p = frappe.db.get_value('Property', args.parent_property, 'project')
		args.project = p
		

	frappe.get_doc(args).insert()

@frappe.whitelist()
def add_multiple_property(data, parent):
	data = json.loads(data)
	new_doc = {'doctype': 'Property', 'parent_property': parent if parent!="All Property" else ""}
	new_doc['project'] = frappe.db.get_value('Property', {"name": parent}, 'project') or ""
	new_doc['company'] = frappe.db.get_value('Property', {"name": parent}, 'company') or ""
	new_doc['cost_center'] = frappe.db.get_value('Property', {"name": parent}, 'cost_center') or ""
	new_doc['parent_property'] = frappe.db.get_value('Property', {"name": parent}, 'parent_property') or ""

	for d in data:
		if not d.get("name"): continue
		new_doc['name'] = d.get("name")
		new_property = frappe.get_doc(new_doc)
		new_property.insert()
		
		
def update_property(doc, method=None):
	property_ = frappe.get_doc('Property', doc.property)
	if method == "on_submit":
		if doc.doctype == "Quotation":
			property_.update({'status': 'Booked', 'quotation': doc.name, 'customer': doc.customer})
		elif doc.doctype == "Sales Order":
			property_.update({'status': 'Initial Contract', 'sales_order': doc.name, 'customer': doc.customer})
		elif doc.doctype == "Contract":
			property_.update({'status': 'Final Contract', 'contract': doc.name, 'customer': doc.party_name})
		elif doc.doctype == "Delivery Note":
			property_.update({'status': 'Delivery Note', 'delivery_note': doc.name, 'customer': doc.customer})
	elif method == "before_cancel":
		customer = None
		if doc.doctype == "Quotation":
			property_.update({'status': 'Available', 'quotation': None, 'customer': customer})
		elif doc.doctype == "Sales Order":
			set_quotation_property(property_)
		elif doc.doctype == "Contract":
			set_sales_order_property(property_)
		elif doc.doctype == "Delivery Note":
			set_contract(property_)
	property_.save()

def set_quotation_property(property_):
	if property_.quotation:
		customer = frappe.db.get_value('Quotation', property_.quotation, 'party_name')
		property_.update({'status': 'Booked', 'sales_order': None, 'customer': customer})
	else:
		property_.update({'status': 'Available', 'sales_order': None, 'customer': customer})

def set_sales_order_property(property_):
	if property_.sales_order:
		customer = frappe.db.get_value('Sales Order', property_.sales_order, 'customer')
		property_.update({'status': 'Initial Contract', 'contract': None, 'customer': customer})
	else:
		set_quotation_property(property_)

def set_contract(property_):
	if property_.contract:
		customer = frappe.db.get_value('Contract', property_.contract, 'party_name')
		property_.update({'status': 'Final Contract', 'delivery_note': None, 'customer': customer})
	else:
		set_sales_order_property(property_)