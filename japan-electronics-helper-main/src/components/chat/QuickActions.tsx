import { QuickAction } from "./types";
import { icons } from "lucide-react";

interface QuickActionsProps {
  actions: QuickAction[];
  onAction: (action: string) => void;
}

const QuickActions = ({ actions, onAction }: QuickActionsProps) => {
  return (
    <div className="flex flex-wrap gap-2 animate-[chat-message-in_0.3s_ease-out]">
      {actions.map((action) => {
        const iconName = action.icon.charAt(0).toUpperCase() + action.icon.slice(1).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
        const LucideIcon = icons[iconName as keyof typeof icons];
        return (
          <button
            key={action.id}
            onClick={() => onAction(action.action)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium bg-chat-quick-action text-chat-quick-action-foreground hover:bg-chat-quick-action-hover transition-colors border border-border/50"
          >
            {LucideIcon && <LucideIcon className="w-4 h-4 text-foreground" />}
            <span>{action.label}</span>
          </button>
        );
      })}
    </div>
  );
};

export default QuickActions;
