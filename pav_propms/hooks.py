# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "pav_propms"
app_title = "PAV Property Management Solution"
app_publisher = "Patrner Team"
app_description = "PAV Property Management Solution"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "email@example.com"
app_license = "MIT"

# Includes in <head>
# ------------------


# include js, css files in header of desk.html
# app_include_css = "/assets/pav_propms/css/pav_propms.css"
# app_include_js = "/assets/pav_propms/js/pav_propms.js"

# include js, css files in header of web template
# web_include_css = "/assets/pav_propms/css/pav_propms.css"
# web_include_js = "/assets/pav_propms/js/pav_propms.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Material Request" : "public/js/material_request.js",
			  "Purchase Order" : "public/js/purchase_order.js",
			  "Purchase Invoice" : "public/js/purchase_invoice.js",
			  "Sales Invoice" : "public/js/sales_invoice.js",
			}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "pav_propms.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "pav_propms.install.before_install"
# after_install = "pav_propms.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "pav_propms.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Quotation": {
		"on_submit": "pav_propms.pav_property_management_solution.doctype.property.property.update_property",
		"before_cancel": "pav_propms.pav_property_management_solution.doctype.property.property.update_property",
	},
    "Sales Order": {
		"on_submit": "pav_propms.pav_property_management_solution.doctype.property.property.update_property",
		"before_cancel": "pav_propms.pav_property_management_solution.doctype.property.property.update_property",
	},
    "Contract": {
		"on_submit": "pav_propms.pav_property_management_solution.doctype.property.property.update_property",
		"before_cancel": "pav_propms.pav_property_management_solution.doctype.property.property.update_property",
	},
    "Delivery Note": {
		"on_submit": "pav_propms.pav_property_management_solution.doctype.property.property.update_property",
		"before_cancel": "pav_propms.pav_property_management_solution.doctype.property.property.update_property",
	},
	"Payment Entry": {
		"validate": "pav_propms.crud_events.validate_ref_express",
	},
	"Material Request": {
		"validate": "pav_propms.crud_events.validate_material_request_item_qty",
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"pav_propms.tasks.all"
# 	],
# 	"daily": [
# 		"pav_propms.tasks.daily"
# 	],
# 	"hourly": [
# 		"pav_propms.tasks.hourly"
# 	],
# 	"weekly": [
# 		"pav_propms.tasks.weekly"
# 	]
# 	"monthly": [
# 		"pav_propms.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "pav_propms.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "pav_propms.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "pav_propms.task.get_dashboard_data"
# }

override_doctype_class = {
    "Purchase Invoice": "pav_propms.overrides.purchase_invoice.CustomPurchaseInvoice",
	"Sales Invoice": "pav_propms.overrides.sales_invoice.CustomSalesInvoice",
	"Payment Entry": "pav_propms.overrides.payment_entry.CustomPaymentEntry",
}

fixtures = [
	"Custom Field", "Custom Script", "Print Format"
]

