# Copyright (c) 2021, Farouk Muharram and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate, cstr
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions, get_dimension_with_children
from erpnext.accounts.report.financial_statements import get_additional_conditions

def execute(filters=None):
	if not filters:
		filters = {}
	
	validate_filters(filters)
	data = get_data(filters)
	columns = get_columns(filters)
	
	return columns, data

def validate_filters(filters):
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date cannot be greater than To Date"))

def get_data(filters):
	budget_against = frappe.scrub(filters.get("budget_against"))
	public_conditions, public_filters = get_condition(filters, budget_against)

	data = []
	opening_balances = get_opening_balances(filters, public_conditions, public_filters)	

	gl_entries_by_account = set_gl_entries_by_account(filters, public_conditions, public_filters)
	

	for gl in gl_entries_by_account:
		debit = gl.debit
		credit = gl.credit
		
		opening_credit = 0
		opening_debit = 0

		opening_debit = opening_balances.get(gl.name, {}).get("opening_debit", 0)
		opening_credit = opening_balances.get(gl.name, {}).get("opening_credit", 0)
		opening_debit, opening_credit = toggle_debit_credit(opening_debit, opening_credit)

		closing_debit, closing_credit = toggle_debit_credit(opening_debit + debit, opening_credit + credit)


		if filters.budget_against != "Project Activities":
			data.append([gl.name, gl.project_activities_name, opening_debit, opening_credit, debit, credit, closing_debit, closing_credit])
		else:
			data.append([gl.name, opening_debit, opening_credit, debit, credit, closing_debit, closing_credit])


	budget_against_doctype = filters.get("budget_against")

	other_filters = {}
	if "budget_against_filter" in filters and filters["budget_against_filter"]:
		other_filters["name"] = ["in", filters["budget_against_filter"]]
	if "company" in filters and filters["company"] and budget_against_doctype != "Project Activities":
		other_filters["company"] = filters["company"]
	if "project" in filters and filters["project"] and budget_against_doctype == "Property":
		other_filters["project"] = filters["project"]

	dim = frappe.get_list(budget_against_doctype, fields = ["name"], filters = other_filters)
	dim = uniqe(gl_entries_by_account, dim)

	for i in dim:
		opening_debit = opening_balances.get(i.name, {}).get("opening_debit", 0)
		opening_credit = opening_balances.get(i.name, {}).get("opening_credit", 0)
		opening_debit, opening_credit = toggle_debit_credit(opening_debit, opening_credit)

		closing_debit, closing_credit = toggle_debit_credit(opening_debit, opening_credit)

		if filters.budget_against != "Project Activities":
			data.append([i.name, "", opening_debit, opening_credit, 0, 0, closing_debit, closing_credit])
		else:
			data.append([i.name, opening_debit, opening_credit, 0, 0, closing_debit, closing_credit])

	return data


def uniqe(items, other_items):
	uniqe_list = []
	for i in other_items:
		if not_found(i, items):
			uniqe_list.append(i)

	return uniqe_list

def not_found(item, entries):
	for i in entries:
		if item["name"] == i["name"]:
			return False

	return True
			
def toggle_debit_credit(debit, credit):
	if flt(debit) > flt(credit):
		debit = flt(debit) - flt(credit)
		credit = 0.0
	else:
		credit = flt(credit) - flt(debit)
		debit = 0.0

	return debit, credit
	
def get_condition(filters, budget_against):
	gl_filters = filters.copy()

	additional_conditions = ''
	if filters.project:
		additional_conditions += " and gl.project = '%s'" % filters.project

	if filters.get("account"):
		lft, rgt = frappe.db.get_value("Account", filters["account"], ["lft", "rgt"])
		additional_conditions += """and gl.account in (select name from tabAccount
		where lft>=%s and rgt<=%s and docstatus<2)""" % (lft, rgt)
	
	elif filters.root_type:
		additional_conditions+= " and acc.root_type in (%s) " % ( ", ".join(["'%s'"] * len(filters.root_type)))
		additional_conditions = additional_conditions % tuple(filters.root_type)
	
	
	if filters.get("property") :
		lft, rgt = frappe.db.get_value("Property", filters["property"], ["lft", "rgt"])
		additional_conditions += """ and gl.property in (select `name` from `tabProperty` 
		WHERE `lft` >= %s AND `rgt` <= %s and docstatus<2)""" % (lft, rgt)
			
	accounting_dimensions = get_accounting_dimensions(as_list=False)
	if accounting_dimensions:
		for dimension in accounting_dimensions:
			if filters.get("budget_against_filter") and budget_against == dimension.fieldname:
				if frappe.get_cached_value('DocType', dimension.document_type, 'is_tree'):
					filters['budget_against_filter'] = get_dimension_with_children(dimension.document_type,
						filters.get('budget_against_filter'))
					additional_conditions += "and gl.{0} in %({0})s".format(dimension.fieldname)
				else:
					additional_conditions += "and gl.{0} in (%({0})s)".format(dimension.fieldname)

				gl_filters.update({
					dimension.fieldname: filters.get('budget_against_filter')
				})
	return additional_conditions, gl_filters


def get_opening_balances(filters, public_conditions, public_filters):
	additional_conditions = ""
	budget_against = frappe.scrub(filters.get("budget_against"))

	query_filters = public_filters.copy()

	additional_conditions += public_conditions

	query_filters.update({
		"company_fb": frappe.db.get_value("Company", filters.company, 'default_finance_book')
	})

	gle = frappe.db.sql("""
		select
			gl.{budget_against} as name, sum(gl.debit) as opening_debit, sum(gl.credit) as opening_credit
		from `tabGL Entry` gl 
		INNER JOIN `tabAccount` acc on gl.account=acc.name 
		where
			gl.company=%(company)s
			{additional_conditions}
			and (gl.posting_date < %(from_date)s or ifnull(gl.is_opening, 'No') = 'Yes')
		group by gl.{budget_against}""".format(additional_conditions=additional_conditions, budget_against = budget_against), 
		query_filters , as_dict=True)

	opening = frappe._dict()
	for d in gle:
		opening.setdefault(d.name, d)
	
	return opening


def set_gl_entries_by_account(filters, public_conditions, public_filters):
	additional_conditions = ''
	if filters.from_date:
		additional_conditions += "and posting_date >= %(from_date)s"

	budget_against = frappe.scrub(filters.get("budget_against"))
	
	gl_filters = public_filters.copy()
	additional_conditions += public_conditions

	gl_entries = frappe.db.sql("""select gl.{budget_against} as name, SUM(gl.debit) as debit, SUM(gl.credit) as credit, 
		SUM(gl.debit_in_account_currency) as debit_in_account_currency, SUM(gl.credit_in_account_currency) as credit_in_account_currency,
		act.project_activities_name
		from `tabGL Entry` gl
		INNER JOIN `tabAccount` acc on gl.account=acc.name 
		LEFT JOIN `tabProject Activities` act on gl.project_activities = act.name
		where gl.company=%(company)s
		{additional_conditions}
		and gl.posting_date <= %(to_date)s and ifnull(gl.is_opening, 'No') = 'No'
		group by gl.{budget_against}
		order by gl.{budget_against} DESC""".format(additional_conditions=additional_conditions, budget_against = budget_against),
		 gl_filters, as_dict=True) #nosec


	gl_entries_by_account = {}
	for entry in gl_entries:
		gl_entries_by_account.setdefault(entry.account, []).append(entry)
		
	return gl_entries

def get_columns(filters):
	columns = [
		_(filters.get("budget_against")) + ":Link/%s:120" % (filters.get("budget_against"))		
	]

	if filters.budget_against != "Project Activities":
		columns.append(_('Project Activities') + ":Link/Project Activities:120")

	columns.append("Opening (Dr):Currency:120")
	columns.append("Opening (Cr):Currency:120")
	columns.append("Debit:Currency:120")
	columns.append("Credit:Currency:120")
	columns.append("Closing (Dr):Currency:120")
	columns.append("Closing (Cr):Currency:120")
	return columns
