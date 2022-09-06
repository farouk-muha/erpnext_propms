# -*- coding: utf-8 -*-
# Copyright (c) 2022, Patrner Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.jinja import validate_template
from six import string_types
import json

class InvestmentContractTemplate(Document):
	def validate(self):
		for i in self.investment_contract_details:
			validate_template(i.subject)


@frappe.whitelist()
def get_contract_template(template_name, doc):
	if isinstance(doc, string_types):
		doc = json.loads(doc)

	contract_template = frappe.get_doc("Investment Contract Template", template_name)
	investment_contract_details = []

	for i in contract_template.investment_contract_details:
		subject = frappe.render_template(i.subject, doc)
		investment_contract_details.append({"subject": subject})


	return {
		'contract_template': contract_template,
		'investment_contract_details': investment_contract_details
	}

