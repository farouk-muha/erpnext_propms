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
	if not filters.fiscal_year:
		frappe.throw(_("Fiscal Year {0} is required").format(filters.fiscal_year))

	fiscal_year = frappe.db.get_value("Fiscal Year", filters.fiscal_year, ["year_start_date", "year_end_date"], as_dict=True)
	if not fiscal_year:
		frappe.throw(_("Fiscal Year {0} does not exist").format(filters.fiscal_year))
	else:
		filters.year_start_date = getdate(fiscal_year.year_start_date)
		filters.year_end_date = getdate(fiscal_year.year_end_date)

	if not filters.from_date:
		filters.from_date = filters.year_start_date

	if not filters.to_date:
		filters.to_date = filters.year_end_date

	filters.from_date = getdate(filters.from_date)
	filters.to_date = getdate(filters.to_date)

	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date cannot be greater than To Date"))

	if (filters.from_date < filters.year_start_date) or (filters.from_date > filters.year_end_date):
		frappe.msgprint(_("From Date should be within the Fiscal Year. Assuming From Date = {0}")\
			.format(formatdate(filters.year_start_date)))

		filters.from_date = filters.year_start_date

	if (filters.to_date < filters.year_start_date) or (filters.to_date > filters.year_end_date):
		frappe.msgprint(_("To Date should be within the Fiscal Year. Assuming To Date = {0}")\
			.format(formatdate(filters.year_end_date)))
		filters.to_date = filters.year_end_date

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

		opening_debit= opening_balances.get(gl.name, {}).get("opening_debit", 0)
		opening_credit = opening_balances.get(gl.name, {}).get("opening_credit", 0)

		closing_debit = opening_debit + gl.debit
		closing_credit = opening_credit + gl.credit


		if filters.budget_against != "Project Activities":
			data.append([gl.name, gl.project_activities_name, opening_debit, opening_credit, debit, credit, closing_debit, closing_credit])
		else:
			data.append([gl.name, opening_debit, opening_credit, debit, credit, closing_debit, closing_credit])			

	return data
			
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
		pro = []
		add = frappe.db.sql("""select name from `tabProperty` where name = '%s' or parent_property = '%s'
			""" % (filters.get("property"), filters.get("property")))
		for d in add:
			pro.append(d[0])
		pro=tuple(pro)
		
		if pro:
			additional_conditions += """ and gl.property in (%s)""" % ", ".join(["'%s'"] * len(pro))
			additional_conditions = additional_conditions % tuple(pro)

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
	additional_conditions = " and posting_date >= %(year_start_date)s"
	budget_against = frappe.scrub(filters.get("budget_against"))

	query_filters = public_filters.copy()

	additional_conditions += public_conditions

	query_filters.update({
		"company_fb": frappe.db.get_value("Company", filters.company, 'default_finance_book')
	})

	gle = frappe.db.sql("""
		select
			gl.{budget_against} as name, sum(gl.debit) as opening_debit, sum(gl.credit) as opening_credit, act.project_activities_name
		from `tabGL Entry` gl 
		INNER JOIN `tabAccount` acc on gl.account=acc.name 
		LEFT JOIN `tabProject Activities` act on gl.project_activities = act.name
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
