from datetime import datetime, timedelta
import random
import string

from src.db.client import get_supabase_client
from src.db.repositories.service_visits_repo import (
    create_service_visit,
    add_service_visit_event,
    find_conflicting_visit,
)

# Keep aligned with frontend ScheduleForm slots
ALLOWED_TIME_SLOTS = {
    "09:00 AM",
    "10:00 AM",
    "11:00 AM",
    "12:00 PM",
    "01:00 PM",
    "02:00 PM",
    "03:00 PM",
    "04:00 PM",
    "05:00 PM",
}
MAX_DAYS_AHEAD = 7


def _generate_visit_no(prefix: str = "SV") -> str:
    date_part = datetime.utcnow().strftime("%Y%m%d")
    token = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"{prefix}-{date_part}-{token}"


def _parse_iso_date(raw: str) -> datetime.date:
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except Exception:
        raise ValueError("Invalid date format. Use YYYY-MM-DD.")


def _validate_date_and_time(date_str: str, time_str: str) -> None:
    if time_str not in ALLOWED_TIME_SLOTS:
        raise ValueError("Invalid time slot selected.")

    selected_date = _parse_iso_date(date_str)
    today = datetime.utcnow().date()

    min_date = today + timedelta(days=1)
    max_date = today + timedelta(days=MAX_DAYS_AHEAD)

    if selected_date < min_date:
        raise ValueError("Date must be at least tomorrow.")
    if selected_date > max_date:
        raise ValueError(f"Date must be within the next {MAX_DAYS_AHEAD} days.")

def _resolve_customer_and_order(invoice_number: str, phone: str):
    supabase = get_supabase_client()
    invoice_number = (invoice_number or "").strip()
    phone = (phone or "").strip()

    if not invoice_number and not phone:
        raise ValueError("Enter invoice number or phone number.")

    # Both provided
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
        rows = order_resp.data or []
        if not rows:
            raise ValueError("No order found for this invoice number.")
        if len(rows) > 1:
            raise ValueError("Multiple orders found for this invoice. Please also enter phone number.")
        order = rows[0]

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
    rows = order_resp.data or []
    if not rows:
        raise ValueError("No order found for this phone number.")
    if len(rows) > 1:
        raise ValueError("Multiple orders found for this phone. Please also enter invoice number.")
    return customer, rows[0]

def preview_order_for_visit(invoice_number: str, phone: str) -> dict:
    customer, order = _resolve_customer_and_order(invoice_number, phone)

    return {
        "success": True,
        "message": "Order matched successfully.",
        "invoiceNumber": order.get("invoice_no") or invoice_number,
        "orderNo": order.get("order_no") or "",
        "productName": order.get("product_name") or "N/A",
        "productDescription": order.get("product_description") or "N/A",
    }


def schedule_visit_from_form(
    invoice_number: str,
    phone: str,
    address: str,
    date: str,
    time: str,
) -> dict:
    invoice_number = (invoice_number or "").strip()
    phone = (phone or "").strip()
    address = (address or "").strip()
    date = (date or "").strip()
    time = (time or "").strip()

    if not invoice_number and not phone:
        raise ValueError("Enter invoice number or phone number.")
        
    if not address:
        raise ValueError("Address is required.")

    _validate_date_and_time(date, time)

    customer, order = _resolve_customer_and_order(invoice_number, phone)

    # 3) prevent duplicate active booking for same invoice/date/time
    effective_invoice_no = (order.get("invoice_no") or invoice_number or "").strip()

    conflict = find_conflicting_visit(
        invoice_no=effective_invoice_no,
        scheduled_date=date,
        scheduled_time=time,
    )

    if conflict:
        raise ValueError("A visit is already scheduled for this invoice at the selected date and time.")

    # 4) create visit
    visit_no = _generate_visit_no()
    payload = {
        "visit_no": visit_no,
        "customer_id": customer["id"],
        "order_id": order["id"],
        "order_no": order.get("order_no"),
        "invoice_no": effective_invoice_no,
        "phone": phone,
        "address": address,
        "scheduled_date": date,
        "scheduled_time": time,
        "timezone": "Asia/Karachi",
        "status": "scheduled",
        "source": "chat_widget",
        "notes": "Technician visit scheduled from chat widget form",
    }

    visit = create_service_visit(payload)

    add_service_visit_event(
        {
            "service_visit_id": visit["id"],
            "event_type": "created",
            "old_status": None,
            "new_status": "scheduled",
            "note": "Visit scheduled from web form",
            "created_by": "bot",
        }
    )

    pretty_date = datetime.strptime(date, "%Y-%m-%d").strftime("%b %d, %Y")

    return {
        "success": True,
        "message": "Technician visit scheduled successfully.",
        "visitNumber": visit_no,
        "status": "scheduled",
        "date": pretty_date,
        "time": time,
    }
