from __future__ import unicode_literals
from frappe import _


def get_data():
	return {
		'fieldname': 'material_quantity_request',
		'transactions': [
			{
				'label': _('Material Requests'),
				'items': ['Material Request']
			}
		]
	}