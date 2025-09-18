import frappe
import json
from frappe.query_builder import DocType

@frappe.whitelist()
def create_installation_request(dn, cust, items):
    tech = frappe.db.get_value("Installation Zone", {"Customer":cust}, "preferred_technician")
    if not tech:
        frappe.throw(f'Please Set Technician for Customer <b>{cust}</b>')
    
    items = json.loads(items)
    data = set_requested_items(dn, items)
   
    req_items, is_partial = data["req_items"], data["is_partial"]
    
    ir = frappe.new_doc("Installation Request")
    ir.assigned_technician = tech
    ir.delivery_note = dn
    ir.customer = cust
    ir.status = "Open"
    tot = 0
    
    for row in req_items:
        tot += row.get("qty")
        ir.append("requested_items", {
            "item_code": row.get("item_code"),
            "quantity": row.get("qty"),
        })
    ir.total_quantity = tot
    
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
    ireq = frappe.db.get_all("Installation Request", {"delivery_note": dn}, pluck="name")
    req_items = []
    
    if ireq:
      
        flag = True
        
        ir = DocType("Installation Request")
        iri = DocType("Installation Request Items")
        
        query = (
            frappe.qb.from_(ir).inner_join(iri)
            .on(iri.parent == ir.name)
            .select(iri.item_code, iri.quantity, iri.name, ir.delivery_note)
            .where( (iri.parent.isin(ireq)) & (ir.delivery_note == dn))
            .run(as_dict=1)
        )
       
        grouped = {}
    
        for row in query:
            key = row.get("item_code")   
            qty = row.get("quantity", 0)  
           
            if key not in grouped:
                grouped[key] = {"item_code": key, "qty": 0}

            grouped[key]["qty"] += qty
        
       
        for itemcode in grouped:
            for rowb in items:
                item = grouped[itemcode].get("item_code")
                qty = grouped[itemcode].get("qty")
                if item == rowb.get("item_code") and qty < rowb.get("qty"):
                    req_items.append({"item_code": itemcode, "qty": rowb.get("qty") - qty})
                    flag = False
                    is_partial = True
        if flag:
            frappe.throw(f'<b>Installation Request is created for complete delivery note items</b>')

    else:
        req_items = items
        
    if req_items:
        return {
                "req_items": req_items,
                "is_partial": is_partial
        }