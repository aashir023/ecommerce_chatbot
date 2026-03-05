import { useState } from "react";
import { previewServiceVisitOrder } from "@/lib/api";

interface ScheduleFormProps {
  onSubmit: (data: { date: string; time: string; invoiceNumber: string; phone: string; address: string }) => void;
}

const timeSlots = [
  "09:00 AM",
  "10:00 AM",
  "11:00 AM",
  "12:00 PM",
  "01:00 PM",
  "02:00 PM",
  "03:00 PM",
  "04:00 PM",
  "05:00 PM",
];

type PreviewResult = {
  invoiceNumber: string;
  orderNo: string;
  productName: string;
  productDescription: string;
};

const ScheduleForm = ({ onSubmit }: ScheduleFormProps) => {
  const [invoiceNumber, setInvoiceNumber] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [selectedDate, setSelectedDate] = useState("");
  const [selectedTime, setSelectedTime] = useState("");

  const [isChecking, setIsChecking] = useState(false);
  const [preview, setPreview] = useState<PreviewResult | null>(null);
  const [error, setError] = useState("");

  const handleCheckOrder = async () => {
    const inv = invoiceNumber.trim();
    const ph = phone.trim();
    if (!inv || !ph) return;

    setError("");
    setPreview(null);
    setIsChecking(true);
    try {
      const result = await previewServiceVisitOrder({ invoiceNumber: inv, phone: ph });
      setPreview({
        invoiceNumber: result.invoiceNumber,
        orderNo: result.orderNo,
        productName: result.productName,
        productDescription: result.productDescription,
      });
    } catch (err: any) {
      setError(err?.message || "Could not verify order details.");
    } finally {
      setIsChecking(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!preview || !selectedDate || !selectedTime || !address.trim()) return;

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
      <p className="text-sm font-semibold text-chat-bubble-bot-foreground">🛠️ Schedule Technician Visit</p>

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

      {!preview && (
        <button
          type="button"
          onClick={handleCheckOrder}
          disabled={isChecking || !invoiceNumber.trim() || !phone.trim()}
          className="w-full py-2 rounded-lg text-sm font-semibold bg-primary text-primary-foreground disabled:opacity-50 hover:opacity-90 transition-opacity"
        >
          {isChecking ? "Checking..." : "Check Order"}
        </button>
      )}

      {error && <p className="text-xs text-red-600">{error}</p>}

      {preview && (
        <div className="rounded-lg border border-border bg-chat-bg p-3 space-y-1">
          <p className="text-xs text-muted-foreground">Matched Order</p>
          <p className="text-sm font-semibold">{preview.productName}</p>
          <p className="text-xs text-muted-foreground">Invoice: {preview.invoiceNumber}</p>
          <p className="text-xs text-muted-foreground">Order: {preview.orderNo}</p>
          <p className="text-xs text-muted-foreground">{preview.productDescription}</p>
        </div>
      )}

      <input
        type="text"
        placeholder="Full Address *"
        value={address}
        onChange={(e) => setAddress(e.target.value)}
        required
        disabled={!preview}
        className="w-full px-3 py-2 rounded-lg text-sm bg-chat-bg text-foreground border border-border focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
      />

      <input
        type="date"
        value={selectedDate}
        onChange={(e) => setSelectedDate(e.target.value)}
        required
        disabled={!preview}
        className="w-full px-3 py-2 rounded-lg text-sm bg-chat-bg text-foreground border border-border focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
      />

      <p className="text-[11px] text-muted-foreground -mt-1 leading-tight">
        Select a date within the next 7 days.
      </p>

      <select
        value={selectedTime}
        onChange={(e) => setSelectedTime(e.target.value)}
        required
        disabled={!preview}
        className="w-full px-3 py-2 rounded-lg text-sm bg-chat-bg text-foreground border border-border focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
      >
        <option value="">Select Time Slot *</option>
        {timeSlots.map((slot) => (
          <option key={slot} value={slot}>
            {slot}
          </option>
        ))}
      </select>

      <button
        type="submit"
        disabled={!preview || !selectedDate || !selectedTime || !address.trim()}
        className="w-full py-2 rounded-lg text-sm font-semibold bg-primary text-primary-foreground disabled:opacity-50 hover:opacity-90 transition-opacity"
      >
        Confirm Schedule
      </button>
    </form>
  );
};

export default ScheduleForm;
