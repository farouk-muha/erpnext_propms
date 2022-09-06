# # Copyright (c) 2016, Patrner Team and contributors
# # For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions, get_dimension_with_children

def execute(filters=None):
	columns, data = get_cols(filters), []
	data = get_data(filters)
	return columns, data

def toggle_debit_credit(debit, credit):
	if flt(debit) > flt(credit):
		debit = flt(debit) - flt(credit)
		credit = 0.0
	else:
		credit = flt(credit) - flt(debit)
		debit = 0.0

	return debit, credit

def get_all_children(doctype, docname):
	if not docname or not doctype:
		return
	docname = str(docname)
	lft_rgt = frappe.db.get_value(doctype, docname, ["lft", "rgt"])
	if not lft_rgt:
		return
	children = frappe.get_all(doctype, filters={"lft": [">=", lft_rgt[0]], "rgt": ["<=",lft_rgt[1]]})
	all_children = [c.name for c in children]
	if all_children:
		return all_children
	else: return [docname]

def get_all_property(property):
	return get_all_children("Property", property)

def get_all_accounts(account):
	return get_all_children("Account", account)

def get_cond(filters):
	gl_cond = ""
	prop_cond = ""

	# property condition only
	if "status" in filters and filters["status"]:
		prop_cond += " AND `pr`.`status` = %(status)s "
	if "property_type" in filters and filters["property_type"]:
		prop_cond += " AND `pr`.`property_type` in %(property_type)s "
	if "temporary_booked" in filters:
		prop_cond += " AND `pr`.`temporary_booked` = %(temporary_booked)s "
	if "property" in filters and filters["property"]:
		pr = get_all_property(filters["property"])
		if pr:
			filters["property"] = pr
			prop_cond += " AND `pr`.`name` in ({})"\
					.format(", ".join([frappe.db.escape(d) for d in filters["property"]]))

	# property and gl condition 
	if "customer" in filters and filters["customer"]:
		gl_cond += " AND `gl`.`party` = %(customer)s "
		prop_cond += " AND `pr`.`customer` = %(customer)s "
	if "project" in filters and filters["project"]:
		gl_cond += " AND `gl`.`project` = %(project)s "
		prop_cond += " AND `pr`.`project` = %(project)s "

	# gl condition only 
	if "account" in filters and filters["account"]:
		pr = get_all_accounts(filters["account"])
		if pr:
			filters["account"] = pr
			gl_cond += " AND `gl`.`account` in ({})"\
					.format(", ".join([frappe.db.escape(d) for d in filters["account"]]))

	return gl_cond, prop_cond

def get_key_map_format (property, customer):
	return "{}-{}".format(property, customer)

def get_data(filters):
	gl_cond, prop_cond = get_cond(filters)
	properties = frappe.db.sql("""
		SELECT 
			`pr`.`name`, `pr`.`status`, `pr`.`apartment_price` AS `price`, `pr`.`quotation`, `pr`.`sales_order`, 
			`pr`.`property_type` , `pr`.`customer` , `pr`.`project`
		FROM
			`tabProperty` AS `pr`
		WHERE 
			`pr`.`company` = %(company)s 
			{cond}
	""".format(cond = prop_cond), filters, as_dict = 1)

	property_name = [d.name for d in properties] 

	if property_name:
		gl_cond += " AND `gl`.`property` in ({})"\
			.format(", ".join([frappe.db.escape(d) for d in property_name]))
	gl_map = set_gl_entries_by_property(filters, gl_cond)
	opening_map = get_opening_balances(filters, gl_cond)

	data = []
	for d in properties:
		row = d.copy()
		if row['status'] == "Booked":
			price = frappe.db.get_value("Quotation", {"property": row['name']}, ["apartment_price"])
			if price:
				row['price'] = price
		elif row["status"] in {"Initial Contract", "Final Contract"}:
			price = frappe.db.get_value("Sales Order Item", {"property": row['name']}, ["amount"])
			if price:
				row['price'] = price

		# key = get_key_map_format(p.name, p.customer)
		gl = gl_map.get(row['name'], {}).get(row['customer'], {})
		row['debit'] = gl.get("debit", 0)
		row['credit'] = gl.get("credit", 0)

		opening = opening_map.get(row['name'], {}).get(row['customer'], {})
		opening_debit = opening.get("opening_debit", 0)
		opening_credit = opening.get("opening_credit", 0)

		row['opening_debit'], row['opening_credit'] = toggle_debit_credit(opening_debit, opening_credit)
		row['closing_debit'], row['closing_credit'] = toggle_debit_credit(opening_debit + row['debit'], opening_credit + row['credit'])

		data.append(row)

		if filters.get("show_details") and d.name in gl_map:
			for key, gl in gl_map[d.name].items():
				if gl.party != row['customer']:
					new_row = row.copy()
					new_row['status'] = None
					new_row['price'] = None
					new_row['customer'] = gl.party
					new_row['debit'] = gl.get("debit", 0)
					new_row['credit'] = gl.get("credit", 0)

					opening = opening_map.get(new_row['name'], {}).get(new_row['customer'], {})
					opening_debit = opening.get("opening_debit", 0)
					opening_credit = opening.get("opening_credit", 0)

					new_row['opening_debit'], new_row['opening_credit'] = toggle_debit_credit(opening_debit, opening_credit)
					new_row['closing_debit'], new_row['closing_credit'] = toggle_debit_credit(opening_debit + new_row['debit'],
						opening_credit + new_row['credit'])
					data.append(new_row)
		
	return data

def set_gl_entries_by_property(filters, conditions):
	data = frappe.db.sql("""
		SELECT 
			`gl`.`property`, `gl`.`party`, `gl`.`project`, SUM(`gl`.`debit`) AS `debit`, SUM(`gl`.`credit`) AS `credit`
		FROM
			`tabGL Entry` AS `gl`
		WHERE 
			`gl`.`party_type` = "Customer" AND
			`gl`.`property` IS NOT NULL	AND
			`gl`.`company` = %(company)s AND
			`gl`.`posting_date` >= %(from_date)s and `gl`.`posting_date` <= %(to_date)s  AND
			ifnull(`gl`.`is_opening`, 'No') = 'No' 
			{cond}
		GROUP BY
			`gl`.`property`, `gl`.`party` 
	""".format(cond = conditions), filters, as_dict = 1)

	gl_map = {}
	for d in data:
		gl_map.setdefault(d.property, {}).setdefault(d.party, d)
	
	return gl_map

def get_opening_balances(filters, conditions):
	data = frappe.db.sql("""
		SELECT 
			`gl`.`property`,`gl`.`party` , SUM(`gl`.`debit`) AS `opening_debit`, SUM(`gl`.`credit`) AS `opening_credit`
		FROM
			`tabGL Entry` AS `gl`
		WHERE 
			`gl`.`party_type` = "Customer" AND			
			`gl`.`property` IS NOT NULL AND
			gl.company=%(company)s AND 
			(gl.posting_date < %(from_date)s or ifnull(gl.is_opening, 'No') = 'Yes')  
			{0} 
		GROUP BY
			`gl`.`property`, `gl`.`party` 
	""".format(conditions), filters, as_dict = 1)
	
	opening_map = {}
	for d in data:
		# opening_map.setdefault(get_key_map_format(d.property, d.party), d)
		opening_map.setdefault(d.property, {}).setdefault(d.party, d)

	return opening_map

def get_cols(filters):
	columns = [
		{
			"label": _("Property"),
			"fieldtype": "Link",
			"fieldname": "name",
			"options": "Property",
			"ReadOnly": 1,
			"width": 120
		},
		{
			"label": _("Status"),
			"fieldtype": "Select",
			"fieldname": "status",
			"ReadOnly": 1,
			"width": 120,
		},
		{
			"label": _("Property Type"),
			"fieldtype": "Link",
			"fieldname": "property_type",
			"options": "Property Type",
			"ReadOnly": 1,
			"width": 50
		},
		{
			"label": _("Project"),
			"fieldtype": "Link",
			"fieldname": "project",
			"options": "Project",
			"ReadOnly": 1,
			"width": 150
		},
		{
			"label": _("Customer"),
			"fieldtype": "Link",
			"fieldname": "customer",
			"options": "Customer",
			"ReadOnly": 1,
			"width": 200
		},
		{
			"label": _("Price"),
			"fieldtype": "Currency",
			"fieldname": "price",
			"ReadOnly": 1,
			"width": 100
		},
		{
			"label": _("Opening (Debit)"),
			"fieldtype": "Currency",
			"fieldname": "opening_debit",
			"ReadOnly": 1,
			"width": 100,
		},
		{
			"label": _("Opening (Credit)"),
			"fieldtype": "Currency",
			"fieldname": "opening_credit",
			"ReadOnly": 1,
			"width": 100,
		},
		{
			"label": _("Debit"),
			"fieldtype": "Currency",
			"fieldname": "debit",
			"ReadOnly": 1,
			"width": 100,
		},
		{
			"label": _("Credit"),
			"fieldtype": "Currency",
			"fieldname": "credit",
			"ReadOnly": 1,
			"width": 100,
		},
		{
			"label": _("Closing (Debit)"),
			"fieldtype": "Currency",
			"fieldname": "closing_debit",
			"ReadOnly": 1,
			"width": 100,
		},
		{
			"label": _("Closing (Credit)"),
			"fieldtype": "Currency",
			"fieldname": "closing_credit",
			"ReadOnly": 1,
			"width": 100,
		},
	]
	return columns


# Copyright (c) 2016, Patrner Team and contributors
# For license information, please see license.txt


# import frappe
# from frappe import _
# from frappe.utils import flt

# def execute(filters=None):
# 	columns = get_cols(filters)

# 	#opening_balances = get_opening_balances(filters)	

# 	data = get_data(filters)
# 	return columns, data



# def get_cols(filters):
# 	columns = [
# 		{
# 			"label": _("Property"),
# 			"fieldtype": "Link",
# 			"fieldname": "property",
# 			"options": "Property",
# 			"ReadOnly": 1,
# 			"width": 250
# 		},
# 		{
# 			"label": _("Status"),
# 			"fieldtype": "Select",
# 			"fieldname": "status",
# 			"ReadOnly": 1,
# 			"width": 120,
# 		},
	
# 		{
# 			"label": _("Customer"),
# 			"fieldtype": "Data",
# 			"fieldname": "customer",
# 			"width": 250
# 		},
# 	]
# 	return columns






# def get_data(filters):

# 	properties = frappe.db.sql("""
# 		SELECT 
# 			`pr`.`name` AS `property`,
# 			`so`.`customer` AS `customer`,
# 			`pr`.`status` AS `status`
# 		     FROM
# 			`tabProperty` AS `pr`
# 			LEFT JOIN `tabQuotation Item` AS `qi` on `pr`.`name` = `qi`.`property` and `pr`.`status` = 'Booked'
# 			LEFT JOIN `tabQuotation` AS `qu` on `qi`.`parent` = `qu`.`name` 

# 			LEFT JOIN `tabSales Order Item` AS `si` on `pr`.`name` = `si`.`property` and `pr`.`status` = 'Final Contract'
# 			LEFT JOIN `tabSales Order` AS `so` on `qi`.`parent` = `so`.`name`

# 			LEFT JOIN `tabContract` AS `co` on `pr`.`name` = `co`.`property` and `pr`.`status` = 'Initial Contract'
	
		

# 	""" ,filters, as_dict = 1)

# 	return properties



