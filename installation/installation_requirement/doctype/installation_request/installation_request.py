# Copyright (c) 2025, shahil and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder import DocType


class InstallationRequest(Document):
	def validate(self):
		self.check_zero_qty()
		
	
		
	
	def check_zero_qty(self):
		for row in self.requested_items:
			if row.quantity <=0 :
				frappe.throw(f'<b>The qunatity must be greater than Zero</b>')
	
	def before_save(self):
		#add partial logic here
		self.find_qty_current_allowed()
		dni = frappe.db.get_all("Delivery Note Item", {"parent": self.delivery_note}, ["item_code", "qty"])
		tot = 0
		
		#find currently against this delivery note which ir exists 
		
		
		for row in dni:
			if self.requested_items:
				if row.item_code in [row.item_code for row in self.requested_items]:
					continue
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
					<th>Location</th>
					<th>Quantity</th>
					<th>Photo</th>
				</tr>
		"""

		for row in self.requested_items:
			table += f"""
				<tr>
					<td>{row.item_code}</td>
					<td>{row.get("roomlocation") or ""}</td>
					<td>{row.quantity}</td>
					<td><img src={row.get("image_link")} width=100px height=100px></img></td>
				</tr>
			"""

		table += "</table>"

		frappe.sendmail(
			recipients=[self.assigned_technician],
			subject="Installation Scheduled",
			message=f"Your installation has been scheduled for Customer <b>{self.customer}</b><br><br>{table}"
		)

		frappe.msgprint(f'MESSAGE SENT TO TECHNICIAN <b>{self.assigned_technician}</b>')
	
	def find_qty_current_allowed(self):
		ireq =  frappe.db.get_all("Installation Request", {"delivery_note": self.delivery_note}, pluck="name")
		ir = DocType("Installation Request")
		iri = DocType("Installation Request Items")

		ir_item_exist = (
			frappe.qb.from_(ir).inner_join(iri)
			.on((ir.name == iri.parent))
			.select(iri.item_code, iri.quantity)
			.where( (iri.parent.isin(ireq)) & (ir.delivery_note == self.delivery_note) &(ir.name != self.name))
			.run(as_dict=1)
		)
		
		grouped_per_item, no_irs = {}, True
		
		#per item total qty in all irs
		
		if ir_item_exist:
			no_irs = False
			for row in ir_item_exist:
				key = row.get("item_code")
				qty = row.get("quantity")
				if key not in grouped_per_item:
					grouped_per_item[key] = {"item_code": key, "qty": 0}
				grouped_per_item[key]["qty"] += qty

			
		else:
			for row in self.requested_items:
				grouped_per_item[row.item_code] = {"item_code": row.item_code, "qty": row.quantity}
		
		dni = frappe.db.get_all("Delivery Note Item", {"parent": self.delivery_note}, ["item_code", "qty"])
		violated_qty, err = {}, ""
		
		for row in dni:
			item = row.item_code
			max_qty = row.qty
			curr_qty = grouped_per_item[item]["qty"]
			grouped_per_item[item]["allowed_qty"] = max_qty - curr_qty
			
		for row in self.requested_items:
			allowed = grouped_per_item[row.item_code]["allowed_qty"]
			if row.quantity > allowed:
				diff = row.quantity - allowed
				err += (
                	f' <b><i><span style="color:red;">Item {row.item_code}</span></i></b> '
                	f'exceeds allowed quantity by <b>{diff}</b>.<br>'
            	)

		if not err:
			return
		frappe.throw( "<b>The following items exceed their allowed quantities:</b><br><br>" + err)