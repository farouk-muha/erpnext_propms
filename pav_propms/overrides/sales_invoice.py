import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from erpnext import get_company_currency

class CustomSalesInvoice(SalesInvoice):
    def validate(self):
        super(CustomSalesInvoice, self).validate()
        if self.currency != get_company_currency(self.company) and (self.conversion_rate == 1):
            frappe.throw(_("Exchange Rate cant be 1"))