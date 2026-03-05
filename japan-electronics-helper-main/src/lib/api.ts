const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

function isFailedToFetch(err: unknown) {
  return err instanceof TypeError && /failed to fetch/i.test(err.message);
}

async function fetchWithOneRetry(input: RequestInfo | URL, init?: RequestInit) {
  try {
    return await fetch(input, init);
  } catch (err) {
    if (isFailedToFetch(err)) {
      // one retry only
      return await fetch(input, init);
    }
    throw err;
  }
}


export async function logComplaint(payload: {
  invoiceNumber: string;
  phone: string;
  description: string;
}) {
  const res = await fetchWithOneRetry(`${API_BASE}/complaints/log`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to log complaint");
  return data;
}

export async function previewComplaintOrder(payload: {
  invoiceNumber: string;
  phone: string;
}) {
  const res = await fetchWithOneRetry(`${API_BASE}/complaints/order-preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to preview order");
  return data;
}

export async function trackComplaint(payload: {
  type: "invoice" | "phone" | "complaint";
  identifier: string;
}) {
  const res = await fetchWithOneRetry(`${API_BASE}/complaints/track`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to track complaint");
  return data;
}

export async function scheduleVisit(payload: {
  invoiceNumber: string;
  phone: string;
  address: string;
  date: string;
  time: string;
}) {
  const res = await fetchWithOneRetry(`${API_BASE}/service-visits/schedule`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to schedule visit");
  return data;
}

export async function previewServiceVisitOrder(payload: {
  invoiceNumber: string;
  phone: string;
}) {
  const res = await fetchWithOneRetry(`${API_BASE}/service-visits/order-preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to preview order");
  return data;
}

export async function sendChatMessage(payload: { user_id: string; message: string }) {
  const res = await fetchWithOneRetry(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to send message");
  return data; // { user_id, reply, message_count, ... }
}

export async function clearChatHistory(userId: string) {
  const res = await fetchWithOneRetry(`${API_BASE}/chat/history/${encodeURIComponent(userId)}`, {
    method: "DELETE",
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to clear chat history");
  return data;
}
