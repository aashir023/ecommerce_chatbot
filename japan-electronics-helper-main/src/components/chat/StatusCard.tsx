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

const StatusCard = ({ result }: StatusCardProps) => {
  return (
    <div className="flex items-end gap-2 animate-[chat-message-in_0.3s_ease-out]">
      <div className="w-7 h-7 rounded-full bg-chat-header flex items-center justify-center text-chat-header-foreground text-xs font-bold shrink-0">
        JE
      </div>
      <div className="bg-chat-bubble-bot rounded-2xl rounded-bl-md p-4 shadow-sm max-w-[80%] space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-sm font-semibold text-chat-bubble-bot-foreground">
            Complaint #{result.complaintNumber}
          </p>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColors[result.status]}`}>
            {statusLabels[result.status]}
          </span>
        </div>
        <p className="text-xs text-muted-foreground">{result.description}</p>
        <p className="text-xs text-muted-foreground">Filed on: {result.date}</p>
      </div>
    </div>
  );
};

export default StatusCard;
