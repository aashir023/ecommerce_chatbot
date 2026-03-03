import re

from src.modules.complaints.ai_parser import parse_complaint_message
from src.db.repositories.orders_repo import find_order_by_identifier
from src.db.repositories.complaints_repo import (
    create_complaint,
    add_complaint_event,
    get_complaint_by_case_id,
    get_complaint_events,
)
from src.modules.complaints.case_id import generate_case_id
from src.modules.complaints.workflow import get_state, set_stage, update_state, reset_state


AI_MIN_CONFIDENCE = 0.60
MIN_SUMMARY_LEN = 8

COMPLAINT_KEYWORDS = ["complaint", "issue", "problem", "damaged", "defect", "not working", "broken"]
TRACKING_REGEX = r"\b[A-Z]{2,5}-\d{8}-[A-Z0-9]{4,8}\b"


def is_complaint_intent(message: str) -> bool:
    m = message.lower()
    return any(k in m for k in COMPLAINT_KEYWORDS)


def extract_case_id(message: str) -> str | None:
    match = re.search(TRACKING_REGEX, message.upper())
    return match.group(0) if match else None


def start_complaint_flow(user_id: str) -> str:
    set_stage(user_id, "awaiting_order")
    return "I can help you file a complaint. Please share your Order No or Invoice No."


def _apply_ai_slots(user_id: str, message: str, state: dict) -> dict:
    parsed = parse_complaint_message(message=message, state=state)

    if parsed.get("ok") and parsed.get("confidence", 0) >= AI_MIN_CONFIDENCE:
        updates = {}
        if parsed.get("order_no"):
            updates["order_no"] = str(parsed["order_no"]).strip()
        if parsed.get("invoice_no"):
            updates["invoice_no"] = str(parsed["invoice_no"]).strip()
        if parsed.get("category"):
            updates["category"] = str(parsed["category"]).strip().lower()
        if parsed.get("summary"):
            updates["summary"] = str(parsed["summary"]).strip()

        if updates:
            update_state(user_id, **updates)

    return get_state(user_id)


def _create_case_from_state(user_id: str) -> tuple[bool, str, dict | None]:
    state = get_state(user_id)

    case_id = generate_case_id()
    complaint_payload = {
        "case_id": case_id,
        "customer_id": None,
        "order_id": None,
        "order_no": state.get("order_no"),
        "invoice_no": state.get("invoice_no"),
        "category": state.get("category") or "general",
        "summary": state.get("summary") or "No summary",
        "details": state.get("summary") or "No details",
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
            "note": "Complaint created by chatbot",
            "created_by": "bot",
        }
    )

    reset_state(user_id)

    ui_payload = {
        "type": "complaint_card",
        "mode": "created",
        "case_id": case_id,
        "status": "open",
        "category": complaint_payload["category"],
        "summary": complaint_payload["summary"],
        "order_no": complaint_payload["order_no"],
    }
    return True, f"Your complaint has been logged successfully. Your case ID is {case_id}.", ui_payload


def handle_complaint_flow(user_id: str, message: str) -> tuple[bool, str, dict | None]:
    state = get_state(user_id)
    state = _apply_ai_slots(user_id=user_id, message=message, state=state)

    stage = state["stage"]

    if stage == "idle":
        return False, "", None

    if stage == "awaiting_order":
        order_no = state.get("order_no")
        invoice_no = state.get("invoice_no")

        if not order_no and not invoice_no:
            return True, "Please share your Order No or Invoice No.", None

        order = find_order_by_identifier(order_no=order_no, invoice_no=invoice_no)

        if not order:
            update_state(user_id, order_no=None, invoice_no=None)
            return True, "I couldn't verify that order/invoice. Please recheck and share it again.", None

        update_state(
            user_id,
            order_no=order.get("order_no"),
            invoice_no=order.get("invoice_no"),
        )
        state = get_state(user_id)

        if state.get("category") and state.get("summary") and len(state["summary"]) >= MIN_SUMMARY_LEN:
            return _create_case_from_state(user_id)

        if state.get("category"):
            set_stage(user_id, "awaiting_summary")
            return True, "Order verified. Please provide a short summary of the issue.", None

        set_stage(user_id, "awaiting_category")
        return True, "Order verified. What is the complaint category?", None

    if stage == "awaiting_category":
        if not state.get("category"):
            update_state(user_id, category=message.strip().lower())

        state = get_state(user_id)

        if state.get("summary") and len(state["summary"]) >= MIN_SUMMARY_LEN:
            return _create_case_from_state(user_id)

        set_stage(user_id, "awaiting_summary")
        return True, "Please provide a short summary of the issue.", None

    if stage == "awaiting_summary":
        if not state.get("summary"):
            update_state(user_id, summary=message.strip())

        state = get_state(user_id)
        summary = (state.get("summary") or "").strip()

        if len(summary) < MIN_SUMMARY_LEN:
            return True, "Please share a bit more detail about the issue.", None

        return _create_case_from_state(user_id)

    return False, "", None


def track_complaint(case_id: str) -> tuple[bool, str, dict | None]:
    complaint = get_complaint_by_case_id(case_id)
    if not complaint:
        return False, f"I couldn't find any complaint with case ID {case_id}. Please re-check the ID.", None

    events = get_complaint_events(complaint["id"], limit=1)
    latest_event = events[0] if events else None

    status = complaint.get("status", "open")
    note = latest_event.get("note") if latest_event else "No timeline events yet."

    ui_payload = {
        "type": "complaint_card",
        "mode": "tracking",
        "case_id": complaint["case_id"],
        "status": status,
        "summary": complaint.get("summary"),
        "category": complaint.get("category"),
        "last_event": note,
        "last_updated": complaint.get("updated_at"),
    }

    text = f"Case {complaint['case_id']} is currently '{status}'. Latest update: {note}"
    return True, text, ui_payload

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


def log_complaint_from_form(invoice_number: str, phone: str, description: str) -> dict:
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

    # 3) create complaint
    case_id = generate_case_id()
    summary = (description or "").strip() or "Customer submitted complaint"

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
