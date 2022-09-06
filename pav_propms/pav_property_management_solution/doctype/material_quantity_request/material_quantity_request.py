from __future__ import unicode_literals
from six import string_types, iteritems
import json
import frappe
from frappe.utils import flt, cstr
from frappe.model.document import Document
from frappe.utils import flt, nowdate
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.doctype.stock_entry.stock_entry import get_uom_details, get_warehouse_details
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.setup.doctype.brand.brand import get_brand_defaults
from erpnext.stock.doctype.item.item import get_item_defaults
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.setup.doctype.brand.brand import get_brand_defaults
from erpnext.stock.get_item_details import get_bin_details, get_default_cost_center, get_conversion_factor, get_item_warehouse, \
process_args, validate_item_details, set_valuation_rate, update_barcode_value
from erpnext.stock.doctype.item_manufacturer.item_manufacturer import get_item_manufacturer_part_no


class MaterialQuantityRequest(Document):
	def validate(self):
		for item in self.items:
			item.amount = (item.qty if item.qty else 0) * (item.rate if item.rate else 0)

	def onload(self):
		pass			
	
	def on_submit(self):
		pass

	def on_cancel(self):
		pass
	# def get_item_details(self, args=None, for_update=False):
	# 	item = frappe.db.sql("""select i.name, i.stock_uom, i.description, i.image, i.item_name, i.item_group,
	# 			i.has_batch_no, i.sample_quantity, i.has_serial_no, i.allow_alternative_item,
	# 			id.expense_account, id.buying_cost_center
	# 		from `tabItem` i LEFT JOIN `tabItem Default` id ON i.name=id.parent and id.company=%s
	# 		where i.name=%s
	# 			and i.disabled=0
	# 			and (i.end_of_life is null or i.end_of_life='0000-00-00' or i.end_of_life > %s)""",
	# 		(self.company, args.get('item_code'), nowdate()), as_dict = 1)

	# 	if not item:
	# 		frappe.throw(_("Item {0} is not active or end of life has been reached").format(args.get("item_code")))

	# 	item = item[0]
	# 	item_group_defaults = get_item_group_defaults(item.name, self.company)
	# 	brand_defaults = get_brand_defaults(item.name, self.company)

	# 	ret = frappe._dict({
	# 		'uom'			      	: item.stock_uom,
	# 		'stock_uom'				: item.stock_uom,
	# 		'description'		  	: item.description,
	# 		'image'					: item.image,
	# 		'item_name' 		  	: item.item_name,
	# 		'cost_center'			: get_default_cost_center(args, item, item_group_defaults, brand_defaults, self.company),
	# 		'qty'					: args.get("qty"),
	# 		'transfer_qty'			: args.get('qty'),
	# 		'conversion_factor'		: 1,
	# 		'batch_no'				: '',
	# 		'actual_qty'			: 0,
	# 		'basic_rate'			: 0,
	# 		'serial_no'				: '',
	# 	})

	# 	# update uom
	# 	if args.get("uom") and for_update:
	# 		ret.update(get_uom_details(args.get('item_code'), args.get('uom'), args.get('qty')))

	# 	for company_field, field in {'cost_center': 'cost_center'}.items():
	# 		if not ret.get(field):
	# 			ret[field] = frappe.get_cached_value('Company',  self.company,  company_field)

	# 	args['posting_date'] = self.posting_date

	# 	stock_and_rate = get_warehouse_details(args) if args.get('warehouse') else {}
	# 	ret.update(stock_and_rate)

	# 	return ret

def get_requested_item_qty(material_quantity_request):
	return frappe._dict(frappe.db.sql("""
		select material_quantity_request_item, sum(qty)
		from `tabMaterial Request Item`
		where docstatus = 1
			and material_quantity_request = %s
		group by material_quantity_request_item
	""", material_quantity_request))

@frappe.whitelist()
def make_material_quantity_request(source_name, target_doc=None):
	requested_item_qty = get_requested_item_qty(source_name)
	def update_item(source, target, source_parent):
		# qty is for packed items, because packed items don't have stock_qty field
		qty = source.get("qty")
		target.project = source_parent.project
		target.qty = qty - requested_item_qty.get(source.name, 0)
		target.rate = source.rate
		target.amount = source.amount
		target.description = source.description
		target.stock_qty = flt(target.qty) * flt(target.conversion_factor)

	doc = get_mapped_doc("Material Quantity Request", source_name, {
		"Material Quantity Request": {
			"doctype": "Material Request",
			"validation": {
				"docstatus": ["=", 1]
			}
		},
		"Material Quantity Request Item": {
			"doctype": "Material Request Item",
			"field_map": {
				"name": "material_quantity_request_item",
				"parent": "material_quantity_request"
			},
			"condition": lambda doc: not frappe.db.exists('Product Bundle', doc.item_code) and doc.qty > requested_item_qty.get(doc.name, 0),
			"postprocess": update_item
		}
	}, target_doc)

	
	return doc


@frappe.whitelist()
def get_item_details(args, doc=None, for_validate=False, overwrite_warehouse=True):
	args = process_args(args)
	item = frappe.get_cached_doc("Item", args.item_code)
	validate_item_details(args, item)

	out = get_basic_details(args, item, overwrite_warehouse)

	if isinstance(doc, string_types):
		doc = json.loads(doc)

	if doc:
		args['posting_date'] = doc.get('posting_date')
		args['transaction_date'] = doc.get('transaction_date')

	set_valuation_rate(out, args)

	if out.get("warehouse"):
		out.update(get_bin_details(args.item_code, out.warehouse))

	# update args with out, if key or value not exists
	for key, value in iteritems(out):
		if args.get(key) is None:
			args[key] = value

	if args.doctype == 'Material Quantity Request':
		out.rate = args.rate or out.price_list_rate
		out.amount = flt(args.qty) * flt(out.rate)

	return out

def get_basic_details(args, item, overwrite_warehouse=True):
	if not item:
		item = frappe.get_doc("Item", args.get("item_code"))

	if item.variant_of:
		item.update_template_tables()

	item_defaults = get_item_defaults(item.name, args.company)
	item_group_defaults = get_item_group_defaults(item.name, args.company)
	brand_defaults = get_brand_defaults(item.name, args.company)

	defaults = frappe._dict({
		'item_defaults': item_defaults,
		'item_group_defaults': item_group_defaults,
		'brand_defaults': brand_defaults
	})

	warehouse = get_item_warehouse(item, args, overwrite_warehouse, defaults)
	
	if args.get('doctype') == "Material Request" and not args.get('material_request_type'):
		args['material_request_type'] = frappe.db.get_value('Material Request',
			args.get('name'), 'material_request_type', cache=True)

	#Set the UOM to the Default Sales UOM or Default Purchase UOM if configured in the Item Master
	if not args.get('uom'):
		if args.get('doctype') == 'Material Quantity Request' and args.get('material_request_type') == 'Purchase':
			args.uom = item.purchase_uom if item.purchase_uom else item.stock_uom

	out = frappe._dict({
		"item_code": item.name,
		"item_name": item.item_name,
		"description": cstr(item.description).strip(),
		"image": cstr(item.image).strip(),
		"warehouse": warehouse,
		"cost_center": get_default_cost_center(args, item_defaults, item_group_defaults, brand_defaults),
		'has_serial_no': item.has_serial_no,
		'has_batch_no': item.has_batch_no,
		"batch_no": args.get("batch_no"),
		"uom": args.uom,
		"min_order_qty": flt(item.min_order_qty) if args.doctype == "Material Quantity Request" else "",
		"qty": flt(args.qty) or 1.0,
		"stock_qty": flt(args.qty) or 1.0,
		"price_list_rate": 0.0,
		"base_price_list_rate": 0.0,
		"rate": 0.0,
		"base_rate": 0.0,
		"amount": 0.0,
		"base_amount": 0.0,
		"net_rate": 0.0,
		"net_amount": 0.0,
		"discount_percentage": 0.0,
		"is_fixed_asset": item.is_fixed_asset,
		"weight_per_unit":item.weight_per_unit,
		"weight_uom":item.weight_uom,
		"transaction_date": args.get("transaction_date")
	})

	# calculate conversion factor
	if item.stock_uom == args.uom:
		out.conversion_factor = 1.0
	else:
		out.conversion_factor = args.conversion_factor or \
			get_conversion_factor(item.name, args.uom).get("conversion_factor")

	args.conversion_factor = out.conversion_factor
	out.stock_qty = out.qty * out.conversion_factor

	# calculate last purchase rate
	if args.get('doctype') == "Material Quantity Request":
		from erpnext.buying.doctype.purchase_order.purchase_order import item_last_purchase_rate
		out.last_purchase_rate = item_last_purchase_rate(args.name, args.conversion_rate, item.name, out.conversion_factor)

	# if default specified in item is for another company, fetch from company
	for d in [
		["Cost Center", "cost_center", "cost_center"],
		["Warehouse", "warehouse", ""]]:
			if not out[d[1]]:
				out[d[1]] = frappe.get_cached_value('Company',  args.company,  d[2]) if d[2] else None

	for fieldname in ("item_name", "item_group", "barcodes", "brand", "stock_uom"):
		out[fieldname] = item.get(fieldname)

	if args.get("manufacturer"):
		part_no = get_item_manufacturer_part_no(args.get("item_code"), args.get("manufacturer"))
		if part_no:
			out["manufacturer_part_no"] = part_no
		else:
			out["manufacturer_part_no"] = None
			out["manufacturer"] = None
	else:
		data = frappe.get_value("Item", item.name,
			["default_item_manufacturer", "default_manufacturer_part_no"] , as_dict=1)

		if data:
			out.update({
				"manufacturer": data.default_item_manufacturer,
				"manufacturer_part_no": data.default_manufacturer_part_no
			})

	child_doctype = args.doctype + ' Item'
	meta = frappe.get_meta(child_doctype)
	if meta.get_field("barcode"):
		update_barcode_value(out)

	return out


