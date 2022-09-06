# -*- coding: utf-8 -*-
# Copyright (c) 2022, Patrner Team and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class InvestmentContractType(Document):
	pass

@frappe.whitelist()
def get_contract_type(type_name, doc):
	investment_contract_term = []
	contract_type = frappe.get_doc("Investment Contract Type", type_name)

	return contract_type.investment_contract_term
	for i in contract_type.investment_contract_term:
		investment_contract_term.append({"description": description})


	return {
		'contract_type': contract_type,
		'investment_contract_term': investment_contract_term
	}