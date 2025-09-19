import frappe
import json
from frappe.query_builder import DocType

@frappe.whitelist()
def create_installation_request(dn, cust, items):
    tech = frappe.db.get_value("Installation Zone", {"Customer": cust}, "preferred_technician")
    if not tech:
        frappe.throw(f'Please Set Technician for Customer <b>{cust}</b>')
   
    items = json.loads(items or "[]")
    data = set_requested_items(dn, items)
    req_items, is_partial = data["req_items"], data["is_partial"]

    ir = frappe.new_doc("Installation Request")
    ir.assigned_technician = tech
    ir.delivery_note = dn
    ir.customer = cust
    ir.status = "Open"
    tot = 0

    for row in req_items:
        qty = row.get("qty", 0) or 0
        tot += qty
        ir.append("requested_items", {
            "item_code": row.get("item_code"),
            "quantity": qty,
        })
    ir.total_quantity = tot

   
    ir.insert()
    ir.save()  

    if is_partial:
        frappe.msgprint(
            f"<b style='color:green;'>Partial Installation created</b> "
            f"against <b>{dn}</b> for remaining quantities",
            title="Partial Installation"
        )
    return ir.name


def set_requested_items(dn, items):
    is_partial = False
    req_items = []
    ireq_names = frappe.db.get_all("Installation Request", {"delivery_note": dn, "docstatus": 1}, pluck="name") or []
    prior_qty = {}
    
    if ireq_names:
        ir = DocType("Installation Request")
        iri = DocType("Installation Request Items")
        rows = (
            frappe.qb.from_(ir).inner_join(iri)
            .on(iri.parent == ir.name)
            .select(iri.item_code, iri.quantity)
            .where((iri.parent.isin(ireq_names)) & (ir.delivery_note == dn) & (ir.docstatus == 1))
            .run(as_dict=True)
        ) or []
        for r in rows:
            key = r.get("item_code")
            prior_qty.setdefault(key, 0)
            prior_qty[key] += (r.get("quantity", 0) or 0)

    
    for it in (items or []):
        item_code = it.get("item_code")
        req_qty = it.get("qty") or it.get("quantity") or 0
        already = prior_qty.get(item_code, 0)
        if req_qty > already:
            req_items.append({"item_code": item_code, "qty": req_qty - already})
            is_partial = True

    if ireq_names and not req_items:
        frappe.throw('<b>Installation Request is created for complete delivery note items</b>')

    if not ireq_names and not req_items:
        req_items = items or []

    return {
        "req_items": req_items,
        "is_partial": is_partial
    }