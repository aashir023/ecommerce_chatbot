from src.db.client import get_supabase_client


def find_order_by_identifier(order_no: str | None = None, invoice_no: str | None = None) -> dict | None:
    if not order_no and not invoice_no:
        return None

    supabase = get_supabase_client()

    if order_no:
        resp = supabase.table("orders").select("*").eq("order_no", order_no).limit(1).execute()
        if resp.data:
            return resp.data[0]

    if invoice_no:
        resp = supabase.table("orders").select("*").eq("invoice_no", invoice_no).limit(1).execute()
        if resp.data:
            return resp.data[0]

    return None
