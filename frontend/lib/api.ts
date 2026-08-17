const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface SiteVisitDetails {
  date?: string | null;
  time?: string | null;
  name?: string | null;
  phone?: string | null;
}

export interface FollowUp {
  needed: boolean;
  when?: string | null;
}

export interface LeadSlots {
  configuration?: string | null;
  budget?: string | null;
  budget_fit?: string | null;
  timeline?: string | null;
  purpose?: string | null;
  preferred_language?: string | null;
  interest_level: string;
  objections: string[];
  site_visit_status: string;
  site_visit_details: SiteVisitDetails;
  follow_up: FollowUp;
  opt_out: boolean;
  escalated_to_human: boolean;
  customer_name?: string | null;
  customer_phone?: string | null;
}

export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: string;
}

export interface BookingResult {
  attempted: boolean;
  success: boolean;
  status: string;
  message?: string | null;
  slot?: string | null;
}

export interface Analytics {
  lead_summary: string;
  configuration?: string | null;
  budget?: string | null;
  budget_fit?: string | null;
  interest_level: string;
  timeline?: string | null;
  language_preference?: string | null;
  objections_raised: string[];
  site_visit_status: string;
  site_visit_details: SiteVisitDetails;
  follow_up_required: boolean;
  follow_up_time?: string | null;
  opt_out: boolean;
  escalated_to_human: boolean;
  conversation_outcome: string;
  confidence_notes?: string | null;
}

export async function createSession(): Promise<{
  session_id: string;
  greeting: string;
  slots: LeadSlots;
}> {
  const res = await fetch(`${API_BASE}/api/sessions`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}

export async function sendMessage(
  sessionId: string,
  message: string
): Promise<{
  reply: string;
  slots: LeadSlots;
  booking?: BookingResult | null;
}> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to send message");
  }
  return res.json();
}

export async function endSession(sessionId: string): Promise<{
  session_id: string;
  analytics: Analytics;
}> {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/end`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to end session");
  return res.json();
}

export async function updateBookingMode(
  sessionId: string,
  mode: "success" | "fail"
): Promise<void> {
  const res = await fetch(
    `${API_BASE}/api/sessions/${sessionId}/booking-mode`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode }),
    }
  );
  if (!res.ok) throw new Error("Failed to update booking mode");
}
