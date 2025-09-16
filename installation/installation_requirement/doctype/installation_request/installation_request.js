// Copyright (c) 2025, shahil and contributors
// For license information, please see license.txt

frappe.ui.form.on("Installation Request", {
    refresh: function(frm) {
        if(frm.doc.docstatus == 1){
            frm.add_custom_button("Schedule Installation", function(){
                frm.set_value("status", "Scheduled")
                frm.save()
                frappe.call({
                    doc: frm.doc,  
                    method: "scheduele_and_send_mail",
                    callback:function(r){
                        if(r.message){
                            frappe.msgprint({title: __('Success'),
                                            message: __('Email has been sent to technician and installation is scheduled'),
                                            indicator: 'green'
                                            });
                        }
                        
                    }
                })
            })
        }
    },
	delivery_note:function(frm) {
        frappe.db.get_value("Delivery Note", {"name": frm.doc.delivery_note}, "customer").then(r=>{
            if(r.message){
                 frm.set_value("customer", r.message.customer)
            }
        })
        if(frm.doc.customer){
             frappe.db.get_value("Installation Zone", {"customer":frm.doc.customer}, "preferred_technician").then(r=>{
                if(r.message){
                    frm.set_value("assigned_technician", r.message.preferred_technician)
                }
             })
        }
       
       
	},
    
   

     on_submit: function(frm) {
        if (frm.doc.total_qty > 10) {
            frappe.msgprint({
                title: __("Alert"),
                indicator: "red",
                message: __("Quantity is more than 10!")
            });
        }
     },
    
});

frappe.ui.form.on("Installation Request Items", {
    quantity: function(frm, cdt, cdn) {
        let tot = 0;

        (frm.doc.requested_items || []).forEach(row => {
            tot += row.quantity || 0;
        });

        frm.set_value("total_quantity", tot);
    }
});


