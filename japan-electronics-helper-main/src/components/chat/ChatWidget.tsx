import { useState, useRef, useEffect, useCallback } from "react";
import { logComplaint, trackComplaint, scheduleVisit, sendChatMessage, clearChatHistory } from "@/lib/api";
import { MessageCircle, X, Send, RotateCcw, ArrowLeft, Phone } from "lucide-react";
import { ChatMessage, StatusResult } from "./types";
import { mainQuickActions, serviceCenters, ESCALATION_NUMBER, productFAQs } from "./chatData";
import logo from "@/assets/japan-electronics-logo.png";
import ChatBubble from "./ChatBubble";
import QuickActions from "./QuickActions";
import ComplaintForm from "./ComplaintForm";
import TrackForm from "./TrackForm";
import ScheduleForm from "./ScheduleForm";
import ServiceCenterList from "./ServiceCenterList";
import StatusCard from "./StatusCard";
import TypingIndicator from "./TypingIndicator";

const ChatWidget = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [currentFlow, setCurrentFlow] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const getOrCreateUserId = () => {
  try {
    const existing = localStorage.getItem("je_chat_user_id");
    if (existing) return existing;

    const generated =
      globalThis.crypto && "randomUUID" in globalThis.crypto
        ? globalThis.crypto.randomUUID()
        : `${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;

    const userId = `web_${generated}`;
    localStorage.setItem("je_chat_user_id", userId);
    return userId;
  } catch {
    return `web_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
  }
};

const userIdRef = useRef<string>(getOrCreateUserId());



  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const addBotMessage = useCallback((content: string, delay = 800) => {
    setIsTyping(true);
    return new Promise<void>((resolve) => {
      setTimeout(() => {
        setMessages((prev) => [
          ...prev,
          { id: Date.now().toString(), role: "bot", content, timestamp: new Date() },
        ]);
        setIsTyping(false);
        resolve();
      }, delay);
    });
  }, []);

  const addUserMessage = (content: string) => {
    setMessages((prev) => [
      ...prev,
      { id: Date.now().toString(), role: "user", content, timestamp: new Date() },
    ]);
  };

  const handleOpen = () => {
    setIsOpen(true);
    if (messages.length === 0) {
      showWelcome();
    }
  };

  const showWelcome = async () => {
    await addBotMessage("👋 Welcome to **Japan Electronics** support! How can I help you today?", 500);
    setCurrentFlow("main");
  };

  const handleAction = async (action: string) => {
    setCurrentFlow(action);

    switch (action) {
      case "product-help":
        addUserMessage("I need product help");
        await addBotMessage("Sure! What do you need help with?");
        setCurrentFlow("product-help-options");
        break;

      case "warranty":
        addUserMessage("Warranty info");
        await addBotMessage(productFAQs.warranty);
        setCurrentFlow("main");
        break;

      case "installation":
        addUserMessage("Installation help");
        await addBotMessage(productFAQs.installation);
        setCurrentFlow("main");
        break;

      case "troubleshooting":
        addUserMessage("Troubleshooting");
        await addBotMessage(productFAQs.troubleshooting);
        setCurrentFlow("main");
        break;

      case "log-complaint":
        addUserMessage("I want to log a complaint");
        await addBotMessage("I'll help you log a complaint. Please fill in the details below:");
        setCurrentFlow("complaint-form");
        break;

      case "track-complaint":
        addUserMessage("I want to track my complaint");
        await addBotMessage("Let's find your complaint status. Please enter your details:");
        setCurrentFlow("track-form");
        break;

      case "service-centers":
        addUserMessage("Show me service centers");
        setCurrentFlow("service-centers-list");
        break;

      case "schedule-visit":
        addUserMessage("I want to schedule a technician visit");
        await addBotMessage("Let's schedule a technician visit for you. Please fill in the details:");
        setCurrentFlow("schedule-form");
        break;

      case "escalate":
        addUserMessage("I want to talk to an agent");
        await addBotMessage(
          `I understand you'd like to speak with a human agent. Please call our dedicated support line:\n\n📞 **${ESCALATION_NUMBER}**\n\nOur agents are available **Mon–Sat, 9 AM – 6 PM**.`
        );
        setCurrentFlow("escalate-view");
        break;

      default:
        break;
    }
  };

  const handleComplaintSubmit = async (data: { invoiceNumber: string; phone: string; description: string }) => {
  addUserMessage(
    `Invoice: ${data.invoiceNumber}, Phone: ${data.phone}${data.description ? `, Issue: ${data.description}` : ""}`
  );

  try {
    setIsTyping(true);
    const result = await logComplaint(data);

    await addBotMessage(
      `✅ ${result.message}\n\n` +
      `**Complaint Number:** ${result.complaintNumber}\n` +
      `**Status:** ${result.status}\n` +
      `**Date:** ${result.date}`
    );
  } catch (err: any) {
    await addBotMessage(`❌ ${err?.message || "Could not log complaint. Please try again."}`);
  } finally {
    setIsTyping(false);
    setCurrentFlow("main");
  }
};


  const handleTrackSubmit = async (data: { identifier: string; type: string }) => {
  addUserMessage(`Tracking by ${data.type}: ${data.identifier}`);

  try {
    setIsTyping(true);

    const result = await trackComplaint({
      type: data.type as "invoice" | "phone" | "complaint",
      identifier: data.identifier,
    });

    const statusResult: StatusResult = {
      complaintNumber: result.complaintNumber,
      status: result.status as StatusResult["status"],
      description: result.description,
      date: result.date,
    };

    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: "bot",
        content: "",
        timestamp: new Date(),
        type: "status-result",
        statusResult,
      },
    ]);
  } catch (err: any) {
    await addBotMessage(`❌ ${err?.message || "Could not fetch complaint status."}`);
  } finally {
    setIsTyping(false);
    setCurrentFlow("main");
  }
};


  const handleScheduleSubmit = async (data: { date: string; time: string; invoiceNumber: string; phone: string; address: string }) => {
  addUserMessage(`Schedule visit on ${data.date} at ${data.time}`);

  try {
    setIsTyping(true);

    const result = await scheduleVisit({
      invoiceNumber: data.invoiceNumber,
      phone: data.phone,
      address: data.address,
      date: data.date,
      time: data.time,
    });

    await addBotMessage(
      `✅ ${result.message}\n\n` +
      `**Visit Number:** ${result.visitNumber}\n` +
      `**Status:** ${result.status}\n` +
      `**Date:** ${result.date}\n` +
      `**Time:** ${result.time}\n\n` +
      `Our technician will call you 30 minutes before arrival.`
    );
  } catch (err: any) {
    await addBotMessage(`❌ ${err?.message || "Could not schedule technician visit. Please try again."}`);
  } finally {
    setIsTyping(false);
    setCurrentFlow("main");
  }
};


  const handleSendMessage = async () => {
  const text = inputValue.trim();
  if (!text) return;

  setInputValue("");
  addUserMessage(text);

  try {
    setIsTyping(true);

    const result = await sendChatMessage({
      user_id: userIdRef.current,
      message: text,
    });

    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: "bot",
        content: result.reply,
        timestamp: new Date(),
      },
    ]);

    setCurrentFlow("main");
  } catch (err: any) {
    await addBotMessage(`❌ ${err?.message || "Network issue, please retry."}`, 200);
  } finally {
    setIsTyping(false);
  }
};


  const handleReset = async () => {
  setMessages([]);
  setCurrentFlow(null);

  try {
    await clearChatHistory(userIdRef.current);
  } catch {
    // ignore backend reset failure
  }

  showWelcome();
};


  const handleGoBack = () => {
    setCurrentFlow("main");
  };

  return (
    <>
      {/* FAB */}
      {!isOpen && (
        <button
          onClick={handleOpen}
          className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-chat-fab text-chat-fab-foreground shadow-lg flex items-center justify-center hover:scale-105 transition-transform z-50 animate-[chat-fab-pulse_3s_ease-in-out_infinite]"
          aria-label="Open chat"
        >
          <MessageCircle className="w-6 h-6" />
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div
          className="fixed bottom-6 right-6 w-[380px] max-w-[calc(100vw-2rem)] h-[600px] max-h-[calc(100vh-3rem)] rounded-2xl shadow-2xl flex flex-col overflow-hidden z-50 border border-border/50"
          style={{ animation: "chat-slide-up 0.3s ease-out" }}
        >
          {/* Header */}
          <div className="bg-chat-header px-4 py-3 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              {currentFlow && currentFlow !== "main" && (
                <button
                  onClick={handleGoBack}
                  className="p-1 rounded-lg text-chat-header-foreground/70 hover:bg-chat-header-foreground/10 transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" />
                </button>
              )}
              <img src={logo} alt="Japan Electronics" className="h-8 bg-white rounded px-1" />
              <div>
                <p className="text-sm font-semibold text-chat-header-foreground">Japan Electronics</p>
                <p className="text-xs text-chat-header-foreground/70">Customer Support</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={handleReset}
                className="p-1.5 rounded-lg text-chat-header-foreground/70 hover:bg-chat-header-foreground/10 transition-colors"
                title="Restart conversation"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-lg text-chat-header-foreground/70 hover:bg-chat-header-foreground/10 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-chat-bg">
            {messages.map((msg) => {
              if (msg.type === "status-result" && msg.statusResult) {
                return <StatusCard key={msg.id} result={msg.statusResult} />;
              }
              return <ChatBubble key={msg.id} message={msg} />;
            })}

            {/* Dynamic content based on flow */}
            {!isTyping && currentFlow === "main" && (
              <QuickActions actions={mainQuickActions} onAction={handleAction} />
            )}
            {!isTyping && currentFlow === "complaint-form" && (
              <div className="space-y-2">
                <ComplaintForm onSubmit={handleComplaintSubmit} />
                <button onClick={handleGoBack} className="text-xs text-muted-foreground hover:text-foreground transition-colors">← Back to menu</button>
              </div>
            )}
            {!isTyping && currentFlow === "track-form" && (
              <div className="space-y-2">
                <TrackForm onSubmit={handleTrackSubmit} />
                <button onClick={handleGoBack} className="text-xs text-muted-foreground hover:text-foreground transition-colors">← Back to menu</button>
              </div>
            )}
            {!isTyping && currentFlow === "service-centers-list" && (
              <div className="space-y-2">
                <ServiceCenterList centers={serviceCenters} />
                <button onClick={handleGoBack} className="text-xs text-muted-foreground hover:text-foreground transition-colors">← Back to menu</button>
              </div>
            )}
            {!isTyping && currentFlow === "schedule-form" && (
              <div className="space-y-2">
                <ScheduleForm onSubmit={handleScheduleSubmit} />
                <button onClick={handleGoBack} className="text-xs text-muted-foreground hover:text-foreground transition-colors">← Back to menu</button>
              </div>
            )}
            {!isTyping && currentFlow === "escalate-view" && (
              <div className="animate-[chat-message-in_0.3s_ease-out] flex flex-col gap-2">
                <a
                  href={`tel:${ESCALATION_NUMBER.replace(/[^+\d]/g, "")}`}
                  className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-chat-success text-chat-success-foreground font-medium text-sm hover:opacity-90 transition-opacity"
                >
                  <Phone className="w-4 h-4" />
                  Call {ESCALATION_NUMBER}
                </a>
                <button
                  onClick={handleGoBack}
                  className="text-xs text-muted-foreground hover:text-foreground transition-colors"
                >
                  ← Back to menu
                </button>
              </div>
            )}

            {isTyping && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="bg-chat-input-bg px-3 py-3 border-t border-border/50 shrink-0">
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                type="text"
                placeholder="Type your message..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
                className="flex-1 px-3 py-2 rounded-xl text-sm bg-chat-bg text-foreground border border-border focus:outline-none focus:ring-2 focus:ring-primary/30 placeholder:text-muted-foreground"
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputValue.trim()}
                className="p-2 rounded-xl bg-primary text-primary-foreground disabled:opacity-40 hover:opacity-90 transition-opacity"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatWidget;
