import { useState } from "react";

interface TrackFormProps {
  onSubmit: (data: { identifier: string; type: string }) => void;
}

const TrackForm = ({ onSubmit }: TrackFormProps) => {
  const [identifier, setIdentifier] = useState("");
  const [type, setType] = useState("invoice");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim()) return;
    onSubmit({ identifier: identifier.trim(), type });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-chat-bubble-bot rounded-2xl rounded-bl-md p-4 shadow-sm animate-[chat-message-in_0.3s_ease-out] space-y-3 max-w-[85%]"
    >
      <p className="text-sm font-semibold text-chat-bubble-bot-foreground">🔍 Track Your Complaint</p>
      <div className="flex gap-2">
        {["invoice", "phone", "complaint"].map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setType(t)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              type === t
                ? "bg-primary text-primary-foreground"
                : "bg-chat-quick-action text-chat-quick-action-foreground"
            }`}
          >
            {t === "invoice" ? "Invoice #" : t === "phone" ? "Phone" : "Complaint #"}
          </button>
        ))}
      </div>
      <input
        type="text"
        placeholder={
          type === "invoice" ? "Enter Invoice Number" : type === "phone" ? "Enter Phone Number" : "Enter Complaint Number"
        }
        value={identifier}
        onChange={(e) => setIdentifier(e.target.value)}
        required
        className="w-full px-3 py-2 rounded-lg text-sm bg-chat-bg text-foreground border border-border focus:outline-none focus:ring-2 focus:ring-primary/30"
      />
      <button
        type="submit"
        className="w-full py-2 rounded-lg text-sm font-semibold bg-primary text-primary-foreground hover:opacity-90 transition-opacity"
      >
        Track Status
      </button>
    </form>
  );
};

export default TrackForm;
