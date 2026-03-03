import { useState } from "react";

interface ComplaintFormProps {
  onSubmit: (data: { invoiceNumber: string; phone: string; description: string }) => void;
}

const ComplaintForm = ({ onSubmit }: ComplaintFormProps) => {
  const [invoiceNumber, setInvoiceNumber] = useState("");
  const [phone, setPhone] = useState("");
  const [description, setDescription] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!invoiceNumber.trim() || !phone.trim()) return;
    onSubmit({ invoiceNumber: invoiceNumber.trim(), phone: phone.trim(), description: description.trim() });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-chat-bubble-bot rounded-2xl rounded-bl-md p-4 shadow-sm animate-[chat-message-in_0.3s_ease-out] space-y-3 max-w-[85%]"
    >
      <p className="text-sm font-semibold text-chat-bubble-bot-foreground">📝 Log a Complaint</p>
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
        placeholder="Describe the issue (optional)"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        rows={2}
        className="w-full px-3 py-2 rounded-lg text-sm bg-chat-bg text-foreground border border-border focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
      />
      <button
        type="submit"
        className="w-full py-2 rounded-lg text-sm font-semibold bg-primary text-primary-foreground hover:opacity-90 transition-opacity"
      >
        Submit Complaint
      </button>
    </form>
  );
};

export default ComplaintForm;
