# Copyright (c) 2013, Farouk and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, formatdate


def execute(filters=None):
    if not filters:
        filters = {}
    columns, data = [], []
    columns = get_columns(filters)

    if filters.get("budget_against_filter"):
        dimensions = filters.get("budget_against_filter")
    
        if filters.get("budget_against") == "Project Activities":
            has_parnt = True
            parent = "parent_project_activities"
        elif filters.get("budget_against") == "Cost Center":
            has_parnt = True
            parent = "parent_cost_center"
        elif filters.get("budget_against") == "Property":
            has_parnt = True
            parent = "parent_property"
        else:
            has_parnt = False
            parent = None

        if has_parnt:
            cond = """ {parent} in (%s)""".format(parent=parent) % ", ".join(["%s"] * len(dimensions))
        
        if has_parnt == True:
            add = frappe.db.sql("""select name from `tab{tab}` where  {cond}
                """.format(tab=filters.get("budget_against"), cond=cond), dimensions)
            for d in add:
                dimensions.append(d[0])
    else:
        dimensions = get_cost_centers(filters)


    dimension_target_details = get_dimension_target_details(
        dimensions, filters)
    # frappe.msgprint("{0}".format(dimension_target_details))
    for ccd in dimension_target_details:
        if not ccd.actual_qty:
            ccd.actual_qty = 0
        if not ccd.planned_qty:
            ccd.planned_qty = 0
        
        sum = 0
        if ccd.planned_qty != 0:
           sum = (ccd.planned_qty-ccd.actual_qty)/ccd.planned_qty*100
        
        if filters.budget_against != "Project Activities":
            data.append([ccd.budget_against_name, ccd.project_activities_name, ccd.item_code, ccd.item_name, ccd.planned_qty,
                     ccd.actual_qty, (ccd.planned_qty-ccd.actual_qty), sum, ccd.doctype])
        else:
            data.append([ccd.project_activities_name, ccd.item_code, ccd.item_name, ccd.planned_qty,
                     ccd.actual_qty, (ccd.planned_qty-ccd.actual_qty), sum, ccd.doctype])
    return columns, data


def get_columns(filters):
    columns = []
    if filters.budget_against != "Project Activities":
        columns.append(_(filters.get("budget_against")) + ":Link/%s:120" % (filters.get("budget_against"))	)
            

    columns.extend ([
            _("Project Activities")+ ":Link/Project Activities:200",
            _('Item') + ":Link/Item:150",
            _('Item Name') + ":Data:150"
            ])

    if filters["value_quantity"] == 'Value':
        columns.append("Planned Amount:Float:100")
        columns.append("Actual Amount:Float:100")
        #columns.append("Variance Qty:Float:100")
        columns.append({
            "fieldname": "variance_qty",
            "label": _("Variance Amount"),
            "fieldtype": "Float",
            "width": 100
        })
    else:
        columns.append("Planned Qty:Float:100")
        columns.append("Actual Qty:Float:100")
        #columns.append("Variance Qty:Float:100")
        columns.append({
            "fieldname": "variance_qty",
            "label": _("Variance Qty"),
            "fieldtype": "Float",
            "width": 100
        })
    columns.append("Variance %:Float:100")

    columns.append({
            "fieldname": "doctype",
            "label": _("Doctype"),
            "fieldtype": "Data",
            "width": 100
        })
    
    return columns


def get_cost_centers(filters):
    order_by = ""
    if filters.get("budget_against") == "Cost Center":
        order_by = "order by lft"

    if filters.get("budget_against") in ["Cost Center", "Project"]:
        return frappe.db.sql_list(
            """
				select
					name
				from
					`tab{tab}`
				where
					company = %s
				{order_by}
			""".format(tab=filters.get("budget_against"), order_by=order_by),
            filters.get("company"))
    else:
        return frappe.db.sql_list(
                """
				select
					name
				from
					`tab{tab}`
			""".format(tab=filters.get("budget_against")))  # nosec
    


def get_dimension_target_details(dimensions, filters):
    budget_against = frappe.scrub(filters.get("budget_against"))
    cond = ""
    
    if filters.get('project'):
        if filters.budget_against == "Property" or filters.budget_against == "Project Activities":
            cond += """and mri.project = %s""" % (frappe.db.escape(filters.get('project')))

    if dimensions:
        cond += """ and mri.{budget_against} in (%s)""".format(
                budget_against=budget_against) % ", ".join(["%s"] * len(dimensions))
        dimensions = dimensions * 3

    dimensions2 = []
    cond2 = ""
    if filters.get("property") and filters.budget_against == "Project Activities" :
        add = frappe.db.sql("""select name from `tabProperty` where name = '%s' or parent_property = '%s'
            """ % (filters.get("property"), filters.get("property")))
        for d in add:
            dimensions2.append(d[0])
        
        cond2 += """ where property in (%s)""" % ", ".join(["%s"] * len(dimensions2))
        # cond2 += """ where property = '%s' """ % filters.get("property")
            
    col = """i.item_name as item_name,
            i.item_code as item_code,
            i.name as name,
            act.name as act_name, act.project_activities_name,
            mri.property,
            mr.name as doc_name, bal.name as budget_against_name""" 
            
    group_by = " group by item_name "

    
    if filters["value_quantity"] == 'Value':
        value_field = 'amount'
    else:
        value_field = 'qty'
    
    if filters["value_quantity"] == 'Value':
        value_field_inv = 'base_amount'
    else:
        value_field_inv = 'qty'
    
    if filters["value_quantity"] == 'Value':
        value_field_purchase = 'base_net_amount'
    else:
        value_field_purchase = 'qty'

    v = frappe.db.sql(
        """
        select
                project_activities_name,
                budget_against_name,
                item_name,
                item_code,
                name,
                sum(planned_qty)  as planned_qty,
                sum(actual_qty)  as actual_qty,
                doctype,
                doc_name
                from
            (
            select
                {col}, 'Material Quantity Request' as doctype, 
                mri.{value_field} as planned_qty,
                0 as actual_qty
            from				
                `tabMaterial Quantity Request Item` mri 
                INNER JOIN `tabItem` i on mri.item_code = i.name 
                INNER JOIN `tabMaterial Quantity Request` mr on mri.parent=mr.name 
                LEFT JOIN `tab{budget_against_label}` bal on mri.{budget_against} = bal.name
                LEFT JOIN `tabProject Activities` act on mri.project_activities = act.name
            where
                i.is_stock_item=1 and mr.company = {company} and mr.docstatus = 1
            and mr.schedule_date between {from_date} and {to_date}
            {cond}
            UNION 

            select
                {col}, 'Stock Entry' as doctype, 
                0 as planned_qty,
                mri.{value_field} as actual_qty
            from				
                `tabStock Entry Detail` mri 
                INNER JOIN `tabItem` i on mri.item_code = i.name 
                INNER JOIN `tabStock Entry` mr on mri.parent=mr.name 
                LEFT JOIN `tab{budget_against_label}` bal on mri.{budget_against} = bal.name
                LEFT JOIN `tabProject Activities` act on mri.project_activities = act.name
                
            where
                i.is_stock_item=1 and mr.company = {company} and mr.docstatus = 1
            and mr.posting_date between {from_date} and {to_date}
            {cond}

             UNION 

            select
                {col}, 'Purchase Invoice' as doctype,  
                0 as planned_qty,
                mri.{value_field_inv} as actual_qty
            from				
                `tabPurchase Invoice Item` mri 
                INNER JOIN `tabItem` i on mri.item_code = i.name 
                INNER JOIN `tabPurchase Invoice` mr on mri.parent=mr.name 
                LEFT JOIN `tab{budget_against_label}` bal on mri.{budget_against} = bal.name
                LEFT JOIN `tabProject Activities` act on mri.project_activities = act.name
                
            where
            i.is_stock_item=0 and mr.company = {company} and mr.docstatus = 1
            and mr.posting_date between {from_date} and {to_date}
            {cond}            
            ) q
            {cond2}
            {group_by}
            order by budget_against_name desc
        """.format(
            value_field=value_field,
            company = frappe.db.escape(filters.company),
            from_date = frappe.db.escape(filters.from_date),
            to_date = frappe.db.escape(filters.to_date),
            budget_against_label=filters.budget_against,
            budget_against=budget_against,
            cond=cond,
            col = col,
            group_by = group_by,
            cond2 = cond2,
            value_field_inv = value_field_inv
        ), tuple(dimensions + dimensions2), as_dict=True)
    return v
