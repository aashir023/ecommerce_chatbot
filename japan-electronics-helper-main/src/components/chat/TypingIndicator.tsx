const TypingIndicator = () => {
  return (
    <div className="flex items-end gap-2 animate-[chat-message-in_0.3s_ease-out]">
      <div className="w-7 h-7 rounded-full bg-chat-header flex items-center justify-center text-chat-header-foreground text-xs font-bold shrink-0">
        JE
      </div>
      <div className="bg-chat-bubble-bot text-chat-bubble-bot-foreground rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
        <div className="flex gap-1.5">
          <span className="w-2 h-2 rounded-full bg-muted-foreground animate-[typing-dot_1.4s_ease-in-out_infinite]" />
          <span className="w-2 h-2 rounded-full bg-muted-foreground animate-[typing-dot_1.4s_ease-in-out_0.2s_infinite]" />
          <span className="w-2 h-2 rounded-full bg-muted-foreground animate-[typing-dot_1.4s_ease-in-out_0.4s_infinite]" />
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;
