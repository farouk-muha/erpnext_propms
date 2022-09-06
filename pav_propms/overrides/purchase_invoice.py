import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice
from erpnext import get_company_currency

# override PurchaseInvoice in hooks
class CustomPurchaseInvoice(PurchaseInvoice):

    # validate conversion_rate if value 1
    def validate(self):
        super(CustomPurchaseInvoice, self).validate()
        if self.currency != get_company_currency(self.company) and (self.conversion_rate == 1):
            frappe.throw(_("Exchange Rate cant be 1"))

    # check journal entry link with field guarantee_jv 
    def on_cancel(self):
        jv = frappe.db.get_value('Journal Entry', {'name': self.guarantee_jv, 'docstatus': 1})
        if jv:
            frappe.throw(_("You have to cancel Journal Entry {0}").format("<a href='#Form/Journal Entry/{0}'>{0}</a>".format(self.guarantee_jv)))
        super(CustomPurchaseInvoice, self).on_cancel()
        stock_entry = frappe.db.get_value('Stock Entry', {'purchase_invoice': self.name, 'docstatus': 1})
        if stock_entry:
            frappe.throw(_("You have to cancel Stock Entry {0}").format("<a href='#Form/Stock Entry/{0}'>{0}</a>".format(stock_entry)))