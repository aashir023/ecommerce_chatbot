from src.db.repositories.complaints_repo import (
    create_complaint,
    add_complaint_event,
    get_complaint_by_case_id,
    get_complaint_events,
)
from src.modules.complaints.case_id import generate_case_id
from datetime import datetime
from src.db.client import get_supabase_client

def _map_status_for_ui(status: str) -> str:
    s = (status or "").lower()
    if s in {"open", "under_review", "awaiting_customer"}:
        return "pending"
    if s in {"in_process", "replacement_shipped"}:
        return "in-progress"
    if s in {"resolved", "closed"}:
        return "resolved"
    if s in {"rejected"}:
        return "escalated"
    return "pending"

def _resolve_customer_and_order(invoice_number: str, phone: str):
    supabase = get_supabase_client()
    invoice_number = (invoice_number or "").strip()
    phone = (phone or "").strip()

    if not invoice_number and not phone:
        raise ValueError("Enter invoice number or phone number.")

    # Both provided: strongest match
    if invoice_number and phone:
        cust_resp = supabase.table("customers").select("*").eq("phone", phone).limit(1).execute()
        customer = cust_resp.data[0] if cust_resp.data else None
        if not customer:
            raise ValueError("No customer found for this phone number.")

        order_resp = (
            supabase.table("orders")
            .select("*")
            .eq("invoice_no", invoice_number)
            .eq("customer_id", customer["id"])
            .limit(1)
            .execute()
        )
        order = order_resp.data[0] if order_resp.data else None
        if not order:
            raise ValueError("Invoice not found for this phone number.")
        return customer, order

    # Invoice only
    if invoice_number:
        order_resp = supabase.table("orders").select("*").eq("invoice_no", invoice_number).limit(2).execute()
        orders = order_resp.data or []
        if not orders:
            raise ValueError("No order found for this invoice number.")
        if len(orders) > 1:
            raise ValueError("Multiple orders found for this invoice. Please also enter phone number.")
        order = orders[0]

        cust_resp = supabase.table("customers").select("*").eq("id", order["customer_id"]).limit(1).execute()
        customer = cust_resp.data[0] if cust_resp.data else None
        if not customer:
            raise ValueError("Customer not found for this invoice.")
        return customer, order

    # Phone only
    cust_resp = supabase.table("customers").select("*").eq("phone", phone).limit(1).execute()
    customer = cust_resp.data[0] if cust_resp.data else None
    if not customer:
        raise ValueError("No customer found for this phone number.")

    order_resp = (
        supabase.table("orders")
        .select("*")
        .eq("customer_id", customer["id"])
        .limit(2)
        .execute()
    )
    orders = order_resp.data or []
    if not orders:
        raise ValueError("No order found for this phone number.")
    if len(orders) > 1:
        raise ValueError("Multiple orders found for this phone. Please also enter invoice number.")
    return customer, orders[0]

def preview_order_from_form(invoice_number: str, phone: str) -> dict:
    customer, order = _resolve_customer_and_order(invoice_number, phone)

    return {
        "success": True,
        "message": "Order matched successfully.",
        "invoiceNumber": order.get("invoice_no") or invoice_number,
        "orderNo": order.get("order_no") or "",
        "productName": order.get("product_name") or "N/A",
        "productDescription": order.get("product_description") or "N/A",
    }


def log_complaint_from_form(invoice_number: str, phone: str, description: str) -> dict:
    customer, order = _resolve_customer_and_order(invoice_number, phone)
    description = (description or "").strip()
    if not description:
        raise ValueError("Description is required.")

    # 3) create complaint
    case_id = generate_case_id()
    summary = description

    complaint_payload = {
        "case_id": case_id,
        "customer_id": customer["id"],
        "order_id": order["id"],
        "order_no": order.get("order_no"),
        "invoice_no": order.get("invoice_no"),
        "category": "general",
        "summary": summary,
        "details": summary,
        "priority": "medium",
        "status": "open",
    }

    complaint = create_complaint(complaint_payload)

    add_complaint_event(
        {
            "complaint_id": complaint["id"],
            "event_type": "created",
            "old_status": None,
            "new_status": "open",
            "note": "Complaint created from web form",
            "created_by": "bot",
        }
    )

    return {
        "success": True,
        "message": "Your complaint has been logged successfully.",
        "complaintNumber": case_id,
        "status": _map_status_for_ui("open"),
        "date": datetime.utcnow().strftime("%b %d, %Y"),
    }


def track_complaint_from_form(track_type: str, identifier: str) -> dict:
    supabase = get_supabase_client()
    complaint = None

    if track_type == "complaint":
        complaint = get_complaint_by_case_id(identifier)

    elif track_type == "invoice":
        resp = (
            supabase.table("complaints")
            .select("*")
            .eq("invoice_no", identifier)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        complaint = resp.data[0] if resp.data else None

    elif track_type == "phone":
        cust_resp = (
            supabase.table("customers")
            .select("id")
            .eq("phone", identifier)
            .limit(1)
            .execute()
        )
        customer = cust_resp.data[0] if cust_resp.data else None
        if customer:
            comp_resp = (
                supabase.table("complaints")
                .select("*")
                .eq("customer_id", customer["id"])
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            complaint = comp_resp.data[0] if comp_resp.data else None

    if not complaint:
        raise ValueError("No complaint found for the provided details.")

    events = get_complaint_events(complaint["id"], limit=1)
    latest_event = events[0] if events else None
    note = latest_event.get("note") if latest_event else "No update yet."

    return {
        "success": True,
        "message": "Complaint status fetched successfully.",
        "complaintNumber": complaint["case_id"],
        "status": _map_status_for_ui(complaint.get("status", "open")),
        "description": note,
        "date": datetime.utcnow().strftime("%b %d, %Y"),
    }
