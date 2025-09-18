// Copyright (c) 2025, shahil and contributors
// For license information, please see license.txt

frappe.query_reports["Customer Installation Items"] = {
	"filters": [

		{
			fieldname:"customer",
			fieldtype:"Link",
			Label: "Customer",
			options:"Customer",
		},
		{
			fieldname:"delivery_note",
			fieldtype:"Link",
			Label: "Delivery Note",
			options:"Delivery Note",
		},
		{
			fieldname:"from_date",
			fieldtype:"Date",
			Label: "From Date"
		},
		{
			fieldname:"to_date",
			fieldtype:"Date",
			Label: "Date",
		},
	]
};
