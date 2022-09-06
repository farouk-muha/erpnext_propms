# -*- coding: utf-8 -*-
# Copyright (c) 2015, Farouk Muharram
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
from erpnext import get_company_currency

# validate if there is doc with same ref and express no
def validate_ref_express(doc, method=None):
    duplcate = None
    if doc.reference_no:
        duplcate = frappe.db.get_value(doc.doctype, {'name' :['!=', doc.name], 'reference_no': doc.reference_no, 'docstatus' :['!=', '2']})
            
    if duplcate:
        frappe.throw(_("{0} {1} has same reference no ").format("<a href='#Form/{0}/{1}'>{1}</a>"
        .format(doc.doctype, duplcate), duplcate))
    elif doc.express_no:
        duplcate = frappe.db.get_value(doc.doctype, {'name' :['!=', doc.name], 'express_no': doc.express_no, 'docstatus' :['!=', '2']})
        if duplcate:
            frappe.throw(_("{0} {1} has same express no ").format("<a href='#Form/{0}/{1}'>{1}</a>"
            .format(doc.doctype, duplcate), duplcate))


# validate material request item qty from material quentity item
def validate_material_request_item_qty(doc, method=None):
    from pav_propms.pav_property_management_solution.doctype.material_quantity_request.material_quantity_request import get_requested_item_qty
    role = frappe.db.get_single_value('Real Estate Settings', 'item_request_qty_allowed')

    roles = frappe.get_roles(frappe.session.user)
    for r in roles:
        if r == 'Administrator' or r == role:
            return

    for item in doc.items:
        if not item.material_quantity_request or not item.material_quantity_request_item:
            continue
        qty = frappe.db.get_value('Material Quantity Request Item', item.material_quantity_request_item, 'qty')
        qty_req = get_requested_item_qty(item.material_quantity_request)
        sum = qty_req.get(item.material_quantity_request_item, 0) + item.qty if qty_req else item.qty
        if qty < sum:
            frappe.throw(_("Quantity at row {0} is more than Material Quantity Request ").format(item.idx))
