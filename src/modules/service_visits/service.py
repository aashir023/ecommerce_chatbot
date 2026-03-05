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

def preview_order_for_visit(invoice_number: str, phone: str) -> dict:
    invoice_number = invoice_number.strip()
    phone = phone.strip()

    supabase = get_supabase_client()

    cust_resp = (
        supabase.table("customers")
        .select("*")
        .eq("phone", phone)
        .limit(1)
        .execute()
    )
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
    invoice_number = invoice_number.strip()
    phone = phone.strip()
    address = address.strip()
    date = date.strip()
    time = time.strip()

    if not invoice_number:
        raise ValueError("Invoice number is required.")
    if not phone:
        raise ValueError("Phone number is required.")
    if not address:
        raise ValueError("Address is required.")

    _validate_date_and_time(date, time)

    supabase = get_supabase_client()

    # 1) find customer by phone
    cust_resp = (
        supabase.table("customers")
        .select("*")
        .eq("phone", phone)
        .limit(1)
        .execute()
    )
    customer = cust_resp.data[0] if cust_resp.data else None
    if not customer:
        raise ValueError("No customer found for this phone number.")

    # 2) find order by invoice + customer
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

    # 3) prevent duplicate active booking for same invoice/date/time
    conflict = find_conflicting_visit(
        invoice_no=invoice_number,
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
        "invoice_no": order.get("invoice_no") or invoice_number,
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
