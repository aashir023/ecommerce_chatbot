import { QuickAction, ServiceCenter } from "./types";

export const mainQuickActions: QuickAction[] = [
  { id: "1", label: "Log Complaint", icon: "edit", action: "log-complaint" },
  { id: "2", label: "Track Complaint", icon: "search", action: "track-complaint" },
  { id: "3", label: "Service Centers", icon: "map-pin", action: "service-centers" },
  { id: "4", label: "Schedule Visit", icon: "calendar", action: "schedule-visit" },
  { id: "5", label: "Talk to Agent", icon: "headset", action: "escalate" },
];

export const serviceCenters: ServiceCenter[] = [
  {
    id: 1,
    name: "Japan Electronics — PWD Rawalpindi",
    address: "Near Punjab Cash & Carry, Main PWD Rd, Rawalpindi",
    phone: "03041111984",
    distance: "N/A",
  },
  {
    id: 2,
    name: "Japan Electronics — Bahria Town Phase 7 Rawalpindi",
    address: "Wallayat Complex, Phase 7, Bahria Town, Rawalpindi",
    phone: "03041111984",
    distance: "N/A",
  },
  {
    id: 3,
    name: "Japan Electronics — Blue Area Islamabad",
    address: "Ajaib & Sons Plaza, Jinnah Ave, Block G, Blue Area, Islamabad",
    phone: "03041111984",
    distance: "N/A",
  },
  {
    id: 4,
    name: "Japan Electronics — Experience Store DHA Phase 2",
    address: "Jan Plaza, GT Road, opposite DHA Phase 2 Gate 2, near Giga Mall, Islamabad",
    phone: "03041111984",
    distance: "N/A",
  },
  {
    id: 5,
    name: "Japan Electronics — Murree Road Rawalpindi",
    address: "Gul Noor Market, Near Naz Cinema, Murree Rd, Rawalpindi",
    phone: "03041111984",
    distance: "N/A",
  },
  {
    id: 6,
    name: "Japan Electronics — Wah Cantt",
    address: "Main GT Road, Opp Savour Foods, Phase 1 Wah Model Town, Wah Cantt",
    phone: "03041111984",
    distance: "N/A",
  },
  {
    id: 7,
    name: "Japan Electronics — Rahwali Gujranwala",
    address: "Opposite Prisma Mall, Main GT Road, Rahwali Cantt, Gujranwala",
    phone: "03041111984",
    distance: "N/A",
  },
  {
    id: 8,
    name: "Japan Electronics — Chandni Chowk Rawalpindi",
    address: "Shop #5, Al Malik Plaza, Chandni Chowk, Rawalpindi",
    phone: "03041111984",
    distance: "N/A",
  },
  {
    id: 9,
    name: "Japan Electronics — Kamra Attock",
    address: "Sajawal Khan Plaza, Main GT Road, Near Shamsabad Road, Qutba Morr, Kamra Kalan",
    phone: "03041111984",
    distance: "N/A",
  },
];


export const ESCALATION_NUMBER = "03041111984";

export const productFAQs: Record<string, string> = {
  warranty: "All Japan Electronics products come with a standard **1-year warranty** from the date of purchase. Extended warranty plans (up to 3 years) are available at any of our service centers. Please keep your original invoice for warranty claims.",
  installation: "We offer **free installation** for all major appliances (ACs, washing machines, refrigerators) within 48 hours of delivery. For smaller products, detailed setup guides are included in the box. Need help? Just schedule a technician visit!",
  troubleshooting: "Here are some common fixes:\n\n• **Device won't turn on** — Check power cable and try a different outlet\n• **Remote not working** — Replace batteries, point directly at sensor\n• **Display issues** — Power cycle the device (unplug for 30 seconds)\n• **Strange noises** — Ensure the device is on a level surface\n\nIf the issue persists, please log a complaint and we'll send a technician.",
};
