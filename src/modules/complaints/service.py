import re

from src.db.repositories.orders_repo import find_order_by_identifier
from src.db.repositories.complaints_repo import (
    create_complaint,
    add_complaint_event,
    get_complaint_by_case_id,
    get_complaint_events,
)
from src.modules.complaints.case_id import generate_case_id
from src.modules.complaints.workflow import get_state, set_stage, update_state, reset_state


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


def handle_complaint_flow(user_id: str, message: str) -> tuple[bool, str, dict | None]:
    state = get_state(user_id)
    stage = state["stage"]

    if stage == "idle":
        return False, "", None

    if stage == "awaiting_order":
        text = message.strip()
        # naive parse: accept as order_no first
        order = find_order_by_identifier(order_no=text) or find_order_by_identifier(invoice_no=text)

        if order:
            update_state(
                user_id,
                order_no=order.get("order_no"),
                invoice_no=order.get("invoice_no"),
            )
            set_stage(user_id, "awaiting_category")
            return True, "Order verified. What is the complaint category? (e.g. product_defect, wrong_item, late_delivery)", None

        # allow no-order complaint fallback
        update_state(user_id, order_no=text)
        set_stage(user_id, "awaiting_category")
        return True, "I could not verify that order right now, but I can still log your complaint. What is the complaint category?", None

    if stage == "awaiting_category":
        update_state(user_id, category=message.strip().lower())
        set_stage(user_id, "awaiting_summary")
        return True, "Please provide a short summary of the issue.", None

    if stage == "awaiting_summary":
        update_state(user_id, summary=message.strip())
        state = get_state(user_id)

        case_id = generate_case_id()
        complaint_payload = {
            "case_id": case_id,
            "customer_id": None,  # link later when customer table mapping is wired
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

        add_complaint_event({
            "complaint_id": complaint["id"],
            "event_type": "created",
            "old_status": None,
            "new_status": "open",
            "note": "Complaint created by chatbot",
            "created_by": "bot",
        })

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
