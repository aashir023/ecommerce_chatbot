import ChatWidget from "@/components/chat/ChatWidget";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      {/* Demo page simulating client's website */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground text-xs font-bold">
              JE
            </div>
            <span className="font-semibold text-foreground text-lg">Japan Electronics</span>
          </div>
          <nav className="hidden md:flex items-center gap-6 text-sm text-muted-foreground">
            <span className="hover:text-foreground cursor-pointer transition-colors">Products</span>
            <span className="hover:text-foreground cursor-pointer transition-colors">Deals</span>
            <span className="hover:text-foreground cursor-pointer transition-colors">Support</span>
            <span className="hover:text-foreground cursor-pointer transition-colors">About</span>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-6 py-20">
        <div className="max-w-2xl mx-auto text-center">
          <h1 className="text-4xl font-bold text-foreground mb-4">
            Welcome to Japan Electronics
          </h1>
          <p className="text-lg text-muted-foreground mb-8">
            Your trusted partner for premium electronics. Need help? Click the chat icon in the bottom-right corner.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-left">
            {[
              { icon: "🛡️", title: "1 Year Warranty", desc: "On all products" },
              { icon: "🚚", title: "Free Delivery", desc: "Same-day available" },
              { icon: "🔧", title: "Expert Support", desc: "24/7 assistance" },
            ].map((item) => (
              <div key={item.title} className="bg-card border border-border rounded-xl p-5">
                <span className="text-2xl">{item.icon}</span>
                <p className="font-semibold text-foreground mt-2">{item.title}</p>
                <p className="text-sm text-muted-foreground">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Chat Widget - embeddable component */}
      <ChatWidget />
    </div>
  );
};

export default Index;
