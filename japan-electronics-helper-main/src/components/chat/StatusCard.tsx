import { StatusResult } from "./types";

interface StatusCardProps {
  result: StatusResult;
}

const statusColors: Record<string, string> = {
  pending: "bg-chat-warning text-chat-warning-foreground",
  "in-progress": "bg-primary text-primary-foreground",
  resolved: "bg-chat-success text-chat-success-foreground",
  escalated: "bg-destructive text-destructive-foreground",
};

const statusLabels: Record<string, string> = {
  pending: "Pending",
  "in-progress": "In Progress",
  resolved: "Resolved",
  escalated: "Escalated",
};

type ParsedReport = {
  product?: string;
  currentStatus?: string;
  update?: string;
  nextStep?: string;
};

function parseReport(description: string): ParsedReport {
  const parts = (description || "")
    .split("|")
    .map((p) => p.trim())
    .filter(Boolean);

  const out: ParsedReport = {};
  for (const part of parts) {
    if (part.startsWith("Product:")) out.product = part.replace("Product:", "").trim();
    else if (part.startsWith("Current status:")) out.currentStatus = part.replace("Current status:", "").trim();
    else if (part.startsWith("Update:")) out.update = part.replace("Update:", "").trim();
    else if (part.startsWith("Next step:")) out.nextStep = part.replace("Next step:", "").trim();
  }
  return out;
}

const StatusCard = ({ result }: StatusCardProps) => {
  const parsed = parseReport(result.description);
  const hasStructuredContent = !!(parsed.product || parsed.update || parsed.nextStep);

  return (
    <div className="flex items-end gap-2 animate-[chat-message-in_0.3s_ease-out]">
      <div className="w-7 h-7 rounded-full bg-chat-header flex items-center justify-center text-chat-header-foreground text-xs font-bold shrink-0">
        JE
      </div>

      <div className="bg-chat-bubble-bot rounded-2xl rounded-bl-md p-4 shadow-sm max-w-[86%] space-y-3 border border-border/40">
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm font-semibold text-chat-bubble-bot-foreground">
            Complaint #{result.complaintNumber}
          </p>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColors[result.status]}`}>
            {statusLabels[result.status]}
          </span>
        </div>

        {hasStructuredContent ? (
          <div className="space-y-2">
            {parsed.product && (
              <div className="rounded-lg bg-background/70 border border-border/50 p-2">
                <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Product</p>
                <p className="text-xs text-foreground font-medium">{parsed.product}</p>
              </div>
            )}

            {parsed.update && (
              <div className="rounded-lg bg-background/70 border border-border/50 p-2">
                <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Latest Update</p>
                <p className="text-xs text-foreground">{parsed.update}</p>
              </div>
            )}

            {parsed.nextStep && (
              <div className="rounded-lg bg-background/70 border border-border/50 p-2">
                <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Next Step</p>
                <p className="text-xs text-foreground">{parsed.nextStep}</p>
              </div>
            )}
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">{result.description}</p>
        )}

        <p className="text-[11px] text-muted-foreground">Filed on: {result.date}</p>
      </div>
    </div>
  );
};

export default StatusCard;
