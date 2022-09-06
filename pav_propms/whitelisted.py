# Copyright (c) 2022, Farouk Muharram
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_default_supplier_query(doctype, txt, searchfield, start, page_len, filters):
    pass