# Copyright (c) 2025, shahil and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class InstallationRequest(Document):
	def validate(self):
		if not self.delivery_note:
			return
		dni = frappe.db.get_all("Delivery Note Item", {"parent": self.delivery_note}, ["item_code", "qty"])
		tot = 0
		
		if self.requested_items:
			return
		
		for row in dni:
			tot += row.get("qty")
			self.append("requested_items", {
					"item_code": row.get("item_code"),
					"quantity": row.get("qty")
			})
		self.total_quantity = tot
	
	@frappe.whitelist()
	def scheduele_and_send_mail(self):
		table = """
			<table border="1" cellspacing="0" cellpadding="5">
				<tr>
					<th>Item Name</th>
					<th>Quantity</th>
				</tr>
			"""
		for row in self.requested_items:
			table += f"""
				<tr>
					<td>{row.item_code}</td>
					<td>{row.quantity}</td>
				</tr>
			"""
		table += "</table>"

		frappe.sendmail(
			recipients=[self.assigned_technician],
			subject="Installation Scheduled",
			message=f"Your installation has been scheduled for Customer <b>{self.customer}</b><br><br>{table}"
		)

		frappe.msgprint(f'MESSAGE SENT TO TECHNICIAN <b>{self.assigned_technician}</b>')

	
		
		

	
