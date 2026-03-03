import { useState, useMemo } from "react";
import { format, addDays } from "date-fns";

interface ScheduleFormProps {
  onSubmit: (data: { date: string; time: string; invoiceNumber: string; phone: string; address: string }) => void;
}

const timeSlots = [
  "09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM",
  "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM",
];

const ScheduleForm = ({ onSubmit }: ScheduleFormProps) => {
  const [selectedDate, setSelectedDate] = useState("");
  const [selectedTime, setSelectedTime] = useState("");
  const [invoiceNumber, setInvoiceNumber] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");

  const availableDates = useMemo(() => {
    const dates = [];
    const today = new Date();
    for (let i = 1; i <= 7; i++) {
      const d = addDays(today, i);
      dates.push({
        value: format(d, "yyyy-MM-dd"),
        label: format(d, "EEE, MMM d"),
      });
    }
    return dates;
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDate || !selectedTime || !invoiceNumber.trim() || !phone.trim() || !address.trim()) return;
    onSubmit({
      date: selectedDate,
      time: selectedTime,
      invoiceNumber: invoiceNumber.trim(),
      phone: phone.trim(),
      address: address.trim(),
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-chat-bubble-bot rounded-2xl rounded-bl-md p-4 shadow-sm animate-[chat-message-in_0.3s_ease-out] space-y-3 max-w-[85%]"
    >
      <p className="text-sm font-semibold text-chat-bubble-bot-foreground">📅 Schedule a Technician Visit</p>

      <input
        type="text"
        placeholder="Invoice Number *"
        value={invoiceNumber}
        onChange={(e) => setInvoiceNumber(e.target.value)}
        required
        className="w-full px-3 py-2 rounded-lg text-sm bg-chat-bg text-foreground border border-border focus:outline-none focus:ring-2 focus:ring-primary/30"
      />
      <input
        type="tel"
        placeholder="Phone Number *"
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
        required
        className="w-full px-3 py-2 rounded-lg text-sm bg-chat-bg text-foreground border border-border focus:outline-none focus:ring-2 focus:ring-primary/30"
      />
      <textarea
        placeholder="Service Address *"
        value={address}
        onChange={(e) => setAddress(e.target.value)}
        required
        rows={2}
        className="w-full px-3 py-2 rounded-lg text-sm bg-chat-bg text-foreground border border-border focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
      />

      <div>
        <p className="text-xs font-medium text-muted-foreground mb-1.5">Select Date</p>
        <div className="flex flex-wrap gap-1.5">
          {availableDates.map((d) => (
            <button
              key={d.value}
              type="button"
              onClick={() => setSelectedDate(d.value)}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                selectedDate === d.value
                  ? "bg-primary text-primary-foreground"
                  : "bg-chat-quick-action text-chat-quick-action-foreground hover:bg-chat-quick-action-hover"
              }`}
            >
              {d.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <p className="text-xs font-medium text-muted-foreground mb-1.5">Select Time</p>
        <div className="flex flex-wrap gap-1.5">
          {timeSlots.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setSelectedTime(t)}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                selectedTime === t
                  ? "bg-primary text-primary-foreground"
                  : "bg-chat-quick-action text-chat-quick-action-foreground hover:bg-chat-quick-action-hover"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <button
        type="submit"
        className="w-full py-2 rounded-lg text-sm font-semibold bg-primary text-primary-foreground hover:opacity-90 transition-opacity"
      >
        Confirm Booking
      </button>
    </form>
  );
};

export default ScheduleForm;
