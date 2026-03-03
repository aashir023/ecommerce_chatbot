import { ChatMessage } from "./types";
import logo from "@/assets/japan-electronics-logo.png";

interface ChatBubbleProps {
  message: ChatMessage;
}

const ChatBubble = ({ message }: ChatBubbleProps) => {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex items-end gap-2 animate-[chat-message-in_0.3s_ease-out] ${
        isUser ? "flex-row-reverse" : ""
      }`}
    >
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-white flex items-center justify-center shrink-0 border border-border/50 overflow-hidden">
          <img src={logo} alt="JE" className="w-5 h-5 object-contain" />
        </div>
      )}
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm ${
          isUser
            ? "bg-chat-bubble-user text-chat-bubble-user-foreground rounded-br-md"
            : "bg-chat-bubble-bot text-chat-bubble-bot-foreground rounded-bl-md"
        }`}
      >
        <MessageContent content={message.content} />
      </div>
    </div>
  );
};

const MessageContent = ({ content }: { content: string }) => {
  // Simple markdown-like bold support
  const parts = content.split(/(\*\*.*?\*\*)/g);
  return (
    <span>
      {parts.map((part, i) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return <strong key={i}>{part.slice(2, -2)}</strong>;
        }
        // Handle newlines
        return part.split("\n").map((line, j, arr) => (
          <span key={`${i}-${j}`}>
            {line}
            {j < arr.length - 1 && <br />}
          </span>
        ));
      })}
    </span>
  );
};

export default ChatBubble;
