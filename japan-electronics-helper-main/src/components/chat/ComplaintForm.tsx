import { useState } from "react";
import { previewComplaintOrder } from "@/lib/api";

interface ComplaintFormProps {
  onSubmit: (data: { invoiceNumber: string; phone: string; description: string }) => void;
}

type PreviewResult = {
  invoiceNumber: string;
  orderNo: string;
  productName: string;
  productDescription: string;
};

const ComplaintForm = ({ onSubmit }: ComplaintFormProps) => {
  const [invoiceNumber, setInvoiceNumber] = useState("");
  const [phone, setPhone] = useState("");
  const [description, setDescription] = useState("");
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
      const result = await previewComplaintOrder({ invoiceNumber: inv, phone: ph });
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
    if (!preview) return;
    onSubmit({
      invoiceNumber: invoiceNumber.trim(),
      phone: phone.trim(),
      description: description.trim(),
    });
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

      {error && (
        <p className="text-xs text-red-600">{error}</p>
      )}

      {preview && (
        <div className="rounded-lg border border-border bg-chat-bg p-3 space-y-1">
          <p className="text-xs text-muted-foreground">Matched Order</p>
          <p className="text-sm font-semibold">{preview.productName}</p>
          <p className="text-xs text-muted-foreground">Invoice: {preview.invoiceNumber}</p>
          <p className="text-xs text-muted-foreground">Order: {preview.orderNo}</p>
          <p className="text-xs text-muted-foreground">{preview.productDescription}</p>
          <p className="text-xs text-green-700 font-medium">Please confirm this is your order by submitting below.</p>
        </div>
      )}

      <textarea
        placeholder="Describe the issue (optional)"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        rows={2}
        className="w-full px-3 py-2 rounded-lg text-sm bg-chat-bg text-foreground border border-border focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
      />

      <button
        type="submit"
        disabled={!preview}
        className="w-full py-2 rounded-lg text-sm font-semibold bg-primary text-primary-foreground disabled:opacity-50 hover:opacity-90 transition-opacity"
      >
        Submit Complaint
      </button>
    </form>
  );
};

export default ComplaintForm;
