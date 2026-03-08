import ChatWidget from "@/components/chat/ChatWidget";

const Index = () => {
  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-white">
      {/* Static clone background */}
      <iframe
        src="/clone-site/index.html"
        title="Japan Electronics Clone Background"
        className="fixed inset-0 h-full w-full border-0"
        style={{ pointerEvents: "auto" }}
      />

      {/* Keep chatbot interactive above background */}
      <div className="relative z-[9999]">
        <ChatWidget />
      </div>
    </div>
  );
};

export default Index;
