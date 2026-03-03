import { QuickAction, ServiceCenter } from "./types";

export const mainQuickActions: QuickAction[] = [
  { id: "1", label: "Log Complaint", icon: "edit", action: "log-complaint" },
  { id: "2", label: "Track Complaint", icon: "search", action: "track-complaint" },
  { id: "3", label: "Service Centers", icon: "map-pin", action: "service-centers" },
  { id: "4", label: "Schedule Visit", icon: "calendar", action: "schedule-visit" },
  { id: "5", label: "Talk to Agent", icon: "headset", action: "escalate" },
];

export const serviceCenters: ServiceCenter[] = [
  { id: 1, name: "Japan Electronics — Connaught Place", address: "Block A, Connaught Place, New Delhi 110001", phone: "+91 11 2341 5678", distance: "2.1 km" },
  { id: 2, name: "Japan Electronics — Lajpat Nagar", address: "22, Central Market, Lajpat Nagar II, New Delhi 110024", phone: "+91 11 2634 7890", distance: "5.4 km" },
  { id: 3, name: "Japan Electronics — Karol Bagh", address: "15/90, WEA, Karol Bagh, New Delhi 110005", phone: "+91 11 2572 3456", distance: "6.2 km" },
  { id: 4, name: "Japan Electronics — Rajouri Garden", address: "J-Block, Rajouri Garden, New Delhi 110027", phone: "+91 11 2510 9876", distance: "8.7 km" },
  { id: 5, name: "Japan Electronics — Dwarka", address: "Sector 12, Dwarka, New Delhi 110078", phone: "+91 11 2509 1234", distance: "15.3 km" },
  { id: 6, name: "Japan Electronics — Noida", address: "Sector 18, Atta Market, Noida 201301", phone: "+91 120 429 5678", distance: "18.1 km" },
  { id: 7, name: "Japan Electronics — Gurgaon", address: "MG Road, DLF Phase 2, Gurgaon 122002", phone: "+91 124 456 7890", distance: "22.5 km" },
  { id: 8, name: "Japan Electronics — Faridabad", address: "NIT, Faridabad, Haryana 121001", phone: "+91 129 225 3456", distance: "25.0 km" },
  { id: 9, name: "Japan Electronics — Ghaziabad", address: "Vaishali, Sector 4, Ghaziabad 201010", phone: "+91 120 267 8901", distance: "20.8 km" },
];

export const ESCALATION_NUMBER = "+91 1800-123-4567";

export const productFAQs: Record<string, string> = {
  warranty: "All Japan Electronics products come with a standard **1-year warranty** from the date of purchase. Extended warranty plans (up to 3 years) are available at any of our service centers. Please keep your original invoice for warranty claims.",
  installation: "We offer **free installation** for all major appliances (ACs, washing machines, refrigerators) within 48 hours of delivery. For smaller products, detailed setup guides are included in the box. Need help? Just schedule a technician visit!",
  troubleshooting: "Here are some common fixes:\n\n• **Device won't turn on** — Check power cable and try a different outlet\n• **Remote not working** — Replace batteries, point directly at sensor\n• **Display issues** — Power cycle the device (unplug for 30 seconds)\n• **Strange noises** — Ensure the device is on a level surface\n\nIf the issue persists, please log a complaint and we'll send a technician.",
};
