export interface ChatMessage {
  id: string;
  role: "user" | "bot";
  content: string;
  timestamp: Date;
  type?: "text" | "quick-actions" | "form" | "service-centers" | "schedule" | "status-result";
  quickActions?: QuickAction[];
  formData?: ComplaintFormData | TrackFormData | ScheduleFormData;
  serviceCenters?: ServiceCenter[];
  statusResult?: StatusResult;
}

export interface QuickAction {
  id: string;
  label: string;
  icon: string;
  action: string;
}

export interface ComplaintFormData {
  invoiceNumber: string;
  phone: string;
  description: string;
}

export interface TrackFormData {
  identifier: string;
  type: "invoice" | "phone" | "complaint";
}

export interface ScheduleFormData {
  date: string;
  time: string;
  invoiceNumber: string;
  phone: string;
  address: string;
}

export interface ServiceCenter {
  id: number;
  name: string;
  address: string;
  phone: string;
  distance?: string;
}

export interface StatusResult {
  complaintNumber: string;
  status: "pending" | "in-progress" | "resolved" | "escalated";
  description: string;
  date: string;
}
