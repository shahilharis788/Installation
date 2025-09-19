frappe.ui.form.on("Delivery Note", {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button("Installation Request", function() {
                create_installation_request(frm);
            }, __("Create"));
        }
    }
});

function create_installation_request(frm) {
    frappe.call({
        method: "installation.tasks.create_installation_request",
        args: {
            dn: frm.doc.name,
            cust: frm.doc.customer,
            items: JSON.stringify(frm.doc.items || [])
        },
        callback: function(response) {
            if (response.message) {
                // route to the created Installation Request form
                frappe.set_route("Form", "Installation Request", response.message);
            }
        }
    });
}
