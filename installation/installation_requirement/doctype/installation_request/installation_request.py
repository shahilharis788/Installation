import json
import frappe
from frappe.model.document import Document
from frappe.query_builder import DocType


class InstallationRequest(Document):
	def validate(self):
		self.check_item_is_dn()
		self.check_zero_qty()
		total = sum([r.quantity for r in self.requested_items]) if self.requested_items else 0
		frappe.db.set_value("Installation Request", self.name, "total_quantity", total)


	def check_zero_qty(self):
		for ri in self.requested_items:
			if ri.quantity <= 0:
				frappe.throw('<b>The quantity must be greater than Zero</b>')


	def check_item_is_dn(self):
		dn_items = frappe.db.get_all("Delivery Note Item", {"parent": self.delivery_note}, pluck="item_code") or []
		dn_item_set = set(dn_items)
		for ri in self.requested_items:
			if ri.item_code not in dn_item_set:
				frappe.throw(f'<b>{ri.item_code}</b> does not belong to given delivery note')


	def before_save(self):
		self.is_qty_greater()
		prior_qty, requested_qty, max_qty = self._compute_qty_maps()
		dn_items = frappe.db.get_all("Delivery Note Item", {"parent": self.delivery_note}, ["item_code", "qty"]) or []
		existing_request_item_codes = {r.item_code for r in self.requested_items}

		for dn_row in dn_items:
			item_code = dn_row.get("item_code")
			allowed_total = dn_row.get("qty", 0)
			already_installed = prior_qty.get(item_code, 0)
			already_requested_in_doc = requested_qty.get(item_code, 0)
			remaining_allowed = allowed_total - already_installed - already_requested_in_doc
			
			if item_code not in existing_request_item_codes and remaining_allowed > 0:
				self.append("requested_items", {
					"item_code": item_code,
					"quantity": remaining_allowed
				})

		if not self.requested_items:
			frappe.throw("No items Found, Already Installed Completely")

	
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
					<td>{row.get('roomlocation') or ""}</td>
					<td>{row.quantity}</td>
					<td><img src="{row.get('image_link') or ''}" width="100" height="100" /></td>
				</tr>
			"""

		table += "</table>"

		frappe.sendmail(
			recipients=[self.assigned_technician],
			subject="Installation Scheduled",
			message=f"Your installation has been scheduled for Customer <b>{self.customer}</b><br><br>{table}"
		)

		frappe.msgprint(f'MESSAGE SENT TO TECHNICIAN <b>{self.assigned_technician}</b>')

	
	def _compute_qty_maps(self):
		prior_qty = {}
		requested_qty = {}
		max_qty = {}

		ireq_names = frappe.db.get_all("Installation Request",
									   filters={"delivery_note": self.delivery_note, "docstatus": 1},
									   pluck="name") or []

		if getattr(self, "name", None):
			ireq_names = [n for n in ireq_names if n != self.name]

		if ireq_names:
			ir = DocType("Installation Request")
			iri = DocType("Installation Request Items")
			rows = (
				frappe.qb.from_(ir).inner_join(iri)
				.on(iri.parent == ir.name)
				.select(iri.item_code, iri.quantity)
				.where((iri.parent.isin(ireq_names)) & (ir.delivery_note == self.delivery_note) & (ir.docstatus == 1))
				.run(as_dict=True)
			) or []
			for r in rows:
				key = r.get("item_code")
				qty = r.get("quantity", 0) or 0
				prior_qty.setdefault(key, 0)
				prior_qty[key] += qty

		for r in (self.requested_items or []):
			requested_qty.setdefault(r.item_code, 0)
			requested_qty[r.item_code] += (r.quantity or 0)

		dn_rows = frappe.db.get_all("Delivery Note Item", {"parent": self.delivery_note}, ["item_code", "qty"]) or []
		for r in dn_rows:
			max_qty[r.get("item_code")] = r.get("qty", 0) or 0

		return prior_qty, requested_qty, max_qty

	
	def is_qty_greater(self):
		prior_qty, requested_qty, max_qty = self._compute_qty_maps()
		errors = []

		for r in (self.requested_items or []):
			item = r.item_code
			req_q = r.quantity or 0
			allowed_total = max_qty.get(item, 0)
			already_installed = prior_qty.get(item, 0)
			allowed_now = allowed_total - already_installed
			if req_q > allowed_now:
				exceed_by = req_q - max(allowed_now, 0)
				errors.append(f'Item <b>{item}</b> requested <b>{req_q}</b> which exceeds allowed remaining quantity by <b>{exceed_by}</b>')

		if errors:
			frappe.throw("<br>".join(errors))
