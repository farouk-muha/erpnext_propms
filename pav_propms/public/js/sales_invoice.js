// Copyright (c) 2022, Farouk Muharram
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on('Sales Invoice', {
	project: function(frm){
		frm.set_value('property', '');
	},

})