# -*- coding: utf-8 -*-
# Copyright (c) 2022, Patrner Team and contributors
# For license information, please see license.txt


import frappe
from datetime import date
from dateutil import relativedelta
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils.data import add_months,month_diff,add_days
from frappe.utils import flt, cint, cstr, today, has_common, random_string, formatdate, getdate, nowdate, get_link_to_form

class InvestmentContract(Document):
	def validate(self):
		pass
		# self.get_investment_contract_term()
	def get_supplier_account(self) :
		su_groub =frappe.db.get_value("Supplier",self.supplier,"supplier_group")
		groub =frappe.get_doc("Supplier Group",su_groub)
		if groub:
			i=0
			for r in groub.accounts:
				if i<1:
					self.account_supplier=r.account
					i+=1

	def get_investment_contract_term(self):
		y,m=0,0
		if self.from_date and self.to_date:
			delta = relativedelta.relativedelta(getdate(self.to_date), getdate(self.from_date))
			# frappe.msgprint("{0}".format(delta))
			y=delta.years
			if y>0:
				if y :
					if y :m=y*12
				if delta.months:
					m+=delta.months
				if delta.days==30:
					m+=1
				
			
				if not self.from_date:
					self.from_date=date.today()

				if self.investment_contract_type=="سنوي":
					if y>0:
						self.get_date(y,"y")				
				if self.investment_contract_type=="نصفي":
					if m>=6:
						self.get_date(m/6,"n")
				if self.investment_contract_type=="ربعي":
					if m>=3:
						self.get_date(m/3,"r")
				if self.investment_contract_type=="شهري":				
					if m>=1:
						self.get_date(m,"m")
			else:
				frappe.msgprint(" الرجاء ان لا تكون الفترة اقل من سنة")
		else:
			frappe.msgprint("To Date is Empty....")
		

	def get_date(self,num,types):
		num=int(num)
		if num and self.amount or self.profit_amount:
			amount= self.profit_amount/num if self.profit_amount else self.amount /num
			if types=="y":p=12	
			elif types=="m":p=1  
			elif types=="r":p=3 
			elif types=="n":p=6
			k=0
			for f in range(0,num):
				k+=p
				row = self.append('investment_contract_term', {})
				row.description="القسط {0}".format(f+1)
				row.due_date=  add_months(self.from_date,k)
				row.amount=amount
		else:
			frappe.msgprint(" Field Amount is Mandatory..{0}.".format(row))
			 


	
	
	

 





@frappe.whitelist()
def make_payment_entry(doc,child):
	from six import string_types
	import json
	if isinstance(doc, string_types):
		self = json.loads(doc)
	childs=frappe.get_doc("Investment Contract Term", child)
	doc = frappe.new_doc("Payment Entry")
	doc.payment_type="Pay"
	doc.party_type="Supplier"
	doc.party=self.get("supplier")
	doc.posting_date=childs.due_date
	doc.paid_amount=childs.amount
	doc.paid_to=self.get("account_supplier")
	doc.paid_to_account_currency=self.get("account_currency")
	doc.project="دوبلكس للمقاولات والتطوير العقاري"
	doc.reference_no=self.get("name")
	doc.reference_date=self.get("date")
	return doc

# @frappe.whitelist()
# def get_supplier_group(supplier):
# 	supplier_group=frappe.db.get_value("Supplier",doc.get("supplier"),"supplier_group")
# 	doc_group =frappe.get_doc("Supplier Group",supplier_group)
# 	return doc_group