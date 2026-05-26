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
    else:
        dimensions = get_cost_centers(filters)

    dimension_target_details = get_dimension_target_details(
        dimensions, filters)
    for ccd in dimension_target_details:
        if not ccd.actual_qty:
            ccd.actual_qty = 0
        if not ccd.planned_qty:
            ccd.planned_qty = 0
        
        sum = 0
        if ccd.planned_qty != 0:
           sum = (ccd.planned_qty-ccd.actual_qty)/ccd.planned_qty*100
        
        data.append([ccd.property_name, ccd.project_activities_name, ccd.item_code, ccd.item_name, ccd.planned_qty,
                     ccd.actual_qty, (ccd.planned_qty-ccd.actual_qty), sum])
    return columns, data


def get_columns(filters):
    
    columns = [
        _("Property")+ ":Data:200",
        _("Project Activities")+ ":Data:200",
        _('Item') + ":Link/Item:150",
        _('Item Name') + ":Data:150"
    ]

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
    cond = ""

    if filters.budget_against == "Property" and filters.get('project'):
    	cond += """and prop.project = %s""" % (frappe.db.escape(filters.get('project')))
    elif filters.budget_against == "Project Activities" and filters.get('project'):
    	cond += """and prop.project = %s""" % (frappe.db.escape(filters.get('project')))

    if dimensions:
        cond += """ and (mri.project_activities in (%s) or mri.property in (%s))""" % (", ".join(["%s"] * len(dimensions)), ", ".join(["%s"] * len(dimensions)))
        dimensions = dimensions * 6

    col = """i.item_name as item_name,
            i.item_code as item_code,
            i.name as name,
            act.name as act_name, act.project_activities_name,
            prop.name as prop_name, prop.property_name"""
            
    group_by = "group by i.name, act.name, prop.name"

    if filters["value_quantity"] == 'Value':
        value_field = 'amount'
    else:
        value_field = 'qty'

    v = frappe.db.sql(
        """
        select
                project_activities_name,
                property_name,
                item_name,
                item_code,
                name,
                sum(planned_qty)  as planned_qty,
                sum(actual_qty)  as actual_qty
                from
            (
                select
                {col},
                sum(mri.{value_field}) as planned_qty,
                0 as actual_qty
            from				
                `tabMaterial Request Item` mri 
                INNER JOIN `tabItem` i on mri.item_code = i.name
                INNER JOIN `tabProject Activities` act on mri.project_activities = act.name
                INNER JOIN `tabProperty` prop on mri.property = prop.name
                INNER JOIN `tabMaterial Request` mr on mri.parent=mr.name 
            where
                i.is_stock_item=1 and mr.company = {company}
            and mr.transaction_date between {from_date} and {to_date}
            {cond}
            {group_by}

            UNION 

            select
                {col},
                0 as planned_qty,
                sum(mri.{value_field}) as actual_qty
            from				
                `tabStock Entry Detail` mri 
                INNER JOIN `tabItem` i on mri.item_code = i.name 
                INNER JOIN `tabProject Activities` act on mri.project_activities = act.name
                INNER JOIN `tabProperty` prop on mri.property = prop.name
                INNER JOIN `tabStock Entry` mr on mri.parent=mr.name 
                
            where
                i.is_stock_item=1 and mr.company = {company}
            and mr.posting_date between {from_date} and {to_date}
            {cond}
            {group_by}

            UNION 

            select
                {col},
                0 as planned_qty,
                sum(mri.{value_field}) as actual_qty
            from				
                `tabPurchase Invoice Item` mri 
                INNER JOIN `tabItem` i on mri.item_code = i.name 
                INNER JOIN `tabProject Activities` act on mri.project_activities = act.name
                INNER JOIN `tabProperty` prop on mri.property = prop.name
                INNER JOIN `tabPurchase Invoice` mr on mri.parent=mr.name 
                
            where
            i.is_stock_item=0 and mr.company = {company}
            and mr.posting_date between {from_date} and {to_date}
            {cond}
            {group_by}
            ) q
            group by name, property_name, project_activities_name
            order by property_name
        """.format(
            value_field=value_field,
            company = frappe.db.escape(filters.company),
            from_date = frappe.db.escape(filters.from_date),
            to_date = frappe.db.escape(filters.to_date),
            cond=cond,
            col = col,
            group_by = group_by,
        ), tuple(dimensions), as_dict=True)
    return v
