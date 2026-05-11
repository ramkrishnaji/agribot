"use client";

import { useState, useRef, useEffect } from "react";
import { 
  Send, Bot, User, Loader2, Leaf, CloudSun, RotateCcw, 
  Menu, X, MessageSquare, Plus, ShoppingCart, ShieldCheck, 
  TrendingUp, Coins, Landmark, Sprout, ChevronRight
} from "lucide-react";
import { UserButton, useUser, SignInButton } from "@clerk/nextjs";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
  role: "user" | "bot";
  content: string;
}

interface ChatSession {
  id: string;
  title: string;
}

const QUICK_ACTIONS = [
  { 
    label: "NHB Subsidy Checker", 
    description: "Check eligibility for 40-50% government support",
    icon: <Landmark className="w-5 h-5 text-emerald-400" />, 
    query: "Tell me about NHB subsidies for new agricultural projects." 
  },
  { 
    label: "High ROI Crops", 
    description: "Investment analysis for Dragon Fruit & Kamalam",
    icon: <TrendingUp className="w-5 h-5 text-blue-400" />, 
    query: "Which crops give the highest ROI with a budget of 5-10 lakhs?" 
  },
  { 
    label: "Polyhouse Strategy", 
    description: "Fan & Pad vs Natural Ventilated ROI",
    icon: <Sprout className="w-5 h-5 text-green-400" />, 
    query: "What is the setup cost and profit for a 1000 sqm polyhouse?" 
  },
  { 
    label: "Live Weather & Rain", 
    description: "Real-time forecast for your specific location",
    icon: <CloudSun className="w-5 h-5 text-yellow-400" />, 
    query: "What is the live weather forecast for my area?" 
  },
];

export default function Home() {
  const { isLoaded, isSignedIn } = useUser();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const fetchSessions = async () => {
    if (isSignedIn) {
      try {
        const response = await axios.get("/api/sessions");
        setSessions(response.data.sessions);
      } catch (err) {
        console.error("Failed to fetch sessions", err);
      }
    }
  };

  useEffect(() => {
    if (isSignedIn) fetchSessions();
  }, [isSignedIn]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = `${inputRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleSubmit = async (e?: React.FormEvent, overrideMessage?: string) => {
    e?.preventDefault();
    const messageToSend = (overrideMessage ?? input).trim();
    if (!messageToSend || isLoading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: messageToSend }]);
    setIsLoading(true);

    try {
      const response = await axios.post("/api/chat", {
        message: messageToSend,
        sessionId: sessionId,
      });

      if (response.data.sessionId && !sessionId) {
        setSessionId(response.data.sessionId);
        fetchSessions();
      }

      setMessages((prev) => [
        ...prev,
        { role: "bot", content: response.data.answer },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          content: "I encountered a technical issue. Please try again or check your connection.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const loadSession = async (id: string) => {
    setIsLoading(true);
    setSessionId(id);
    setIsSidebarOpen(false);
    try {
      const response = await axios.get(`/api/sessions/${id}`);
      setMessages(response.data.messages);
    } catch (err) {
      console.error("Failed to load session", err);
    } finally {
      setIsLoading(false);
    }
  };

  const startNewChat = () => {
    setMessages([]);
    setSessionId(null);
    setIsSidebarOpen(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  if (!isLoaded) return <div className="h-screen bg-[#0c0d0c] flex items-center justify-center"><Loader2 className="animate-spin text-accent-agri/40" /></div>;

  return (
    <div className="h-[100dvh] bg-[#0c0d0c] text-[#f0f2f0] flex font-sans overflow-hidden">
      {/* Sidebar Overlay */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-40 lg:hidden backdrop-blur-sm" 
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`fixed lg:relative inset-y-0 left-0 w-80 bg-[#111211] border-r border-white/5 z-50 transform ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 transition-transform duration-300 ease-out flex flex-col`}>
        <div className="p-6">
          <button 
            onClick={startNewChat}
            className="w-full flex items-center justify-between gap-3 px-4 py-3 rounded-xl bg-accent-agri/10 border border-accent-agri/20 hover:bg-accent-agri/20 transition-all text-sm font-semibold text-accent-agri"
          >
            <div className="flex items-center gap-3">
              <Plus className="w-4 h-4" />
              New Consultation
            </div>
            <ChevronRight className="w-4 h-4 opacity-50" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-2 space-y-1">
          <div className="text-[10px] font-bold text-white/20 uppercase tracking-[0.2em] mb-4 px-4">Consultation History</div>
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => loadSession(s.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left text-sm transition-all ${sessionId === s.id ? 'bg-white/5 border border-white/10 text-white' : 'text-white/40 hover:bg-white/[0.02] hover:text-white/80'}`}
            >
              <MessageSquare className="w-4 h-4 shrink-0 opacity-40" />
              <span className="truncate font-medium">{s.title}</span>
            </button>
          ))}
        </div>

        <div className="p-6 border-t border-white/5 bg-black/20">
          {isSignedIn ? (
            <div className="flex items-center gap-4">
              <UserButton appearance={{ elements: { userButtonAvatarBox: "w-9 h-9 border border-white/10" } }} />
              <div className="text-xs">
                <div className="text-white/90 font-bold tracking-tight">Account Managed</div>
                <div className="text-white/30 font-medium">Premium Access</div>
              </div>
            </div>
          ) : (
            <SignInButton mode="modal">
              <button className="w-full py-2.5 rounded-lg border border-white/10 text-xs font-bold uppercase tracking-widest hover:bg-white/5 transition-all">Unlock Full Analysis</button>
            </SignInButton>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        <header className="glass px-6 py-4 flex items-center justify-between z-30">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setIsSidebarOpen(true)}
              className="lg:hidden p-2 hover:bg-white/5 rounded-xl text-white/40 transition-colors"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-3">
              <div className="bg-gradient-to-br from-accent-agri to-emerald-700 p-2 rounded-xl shadow-lg shadow-accent-agri/10">
                <Leaf className="w-5 h-5 text-white" />
              </div>
              <div className="flex flex-col -space-y-0.5">
                <span className="text-lg font-black tracking-tight text-white/95 uppercase">AgriBot</span>
                <span className="text-[10px] font-bold text-accent-agri/80 uppercase tracking-[0.15em]">Modern Agriculture Consultant</span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-1.5 text-[9px] text-accent-agri/60 bg-accent-agri/5 border border-accent-agri/10 px-2.5 py-1 rounded-full uppercase tracking-[0.2em] font-black">
              <span className="w-1 h-1 rounded-full bg-accent-agri animate-pulse" />
              Live Intelligence v3.0
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto scrollbar-hide bg-[radial-gradient(circle_at_top,_var(--tw-gradient-stops))] from-white/[0.02] via-transparent to-transparent">
          <div className="max-w-[840px] mx-auto px-6 w-full">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center min-h-[85vh] text-center animate-fade-in">
                <div className="relative mb-8">
                  <div className="absolute inset-0 bg-accent-agri/20 blur-3xl rounded-full" />
                  <div className="relative w-20 h-20 bg-gradient-to-br from-accent-agri to-emerald-800 rounded-[2rem] flex items-center justify-center shadow-2xl shadow-accent-agri/20 rotate-3">
                    <Sprout className="w-10 h-10 text-white" />
                  </div>
                </div>
                
                <h1 className="text-4xl font-black mb-4 text-white tracking-tighter sm:text-5xl">
                  Precision Consulting for <span className="text-accent-agri">Modern Farmers.</span>
                </h1>
                <p className="text-white/40 max-w-lg text-sm sm:text-base font-medium leading-relaxed mb-12">
                  Ground-breaking agricultural intelligence powered by verified Indian data. Analyze ROI, check subsidies, and scale your farming business.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-2xl">
                  {QUICK_ACTIONS.map((action) => (
                    <button
                      key={action.label}
                      onClick={() => handleSubmit(undefined, action.query)}
                      className="group flex flex-col items-start gap-3 text-left p-5 rounded-2xl bg-surface-agri/40 border border-white/5 hover:bg-surface-agri/60 hover:border-accent-agri/30 transition-all duration-300"
                    >
                      <div className="p-2.5 rounded-xl bg-white/5 group-hover:bg-accent-agri/10 transition-colors">
                        {action.icon}
                      </div>
                      <div className="space-y-0.5">
                        <div className="text-sm font-bold text-white/90 group-hover:text-accent-agri transition-colors">{action.label}</div>
                        <div className="text-[11px] font-medium text-white/30 leading-snug">{action.description}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="py-12 space-y-8 animate-fade-in">
                {messages.map((msg, idx) => (
                  <div key={idx} className={`relative group ${msg.role === "bot" ? "chat-bubble-bot p-6 rounded-2xl" : ""}`}>
                    <div className="flex gap-6 items-start max-w-[780px] mx-auto">
                      <div className={`w-10 h-10 shrink-0 rounded-xl flex items-center justify-center shadow-lg ${msg.role === "user" ? "bg-white/5 border border-white/10" : "bg-gradient-to-br from-accent-agri to-emerald-800"}`}>
                        {msg.role === "user" ? <User className="w-5 h-5 text-white/40" /> : <Bot className="w-5 h-5 text-white" />}
                      </div>
                      <div className="flex-1 min-w-0 pt-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-[10px] font-black uppercase tracking-widest text-white/20">
                            {msg.role === "user" ? "Client Query" : "AgriBot Intelligence"}
                          </span>
                        </div>
                        <div className="text-[15px] sm:text-[16px] leading-[1.8] text-white/80 prose prose-invert prose-sm max-w-none prose-headings:text-white prose-strong:text-accent-agri prose-ul:list-disc prose-li:marker:text-accent-agri prose-hr:border-white/5">
                          {msg.role === "user" ? (
                            <p className="font-semibold text-white/95">{msg.content}</p>
                          ) : (
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                
                {isLoading && (
                  <div className="py-8 animate-pulse">
                    <div className="flex gap-6 items-start max-w-[780px] mx-auto">
                      <div className="w-10 h-10 shrink-0 rounded-xl bg-accent-agri/10 border border-accent-agri/20 flex items-center justify-center">
                        <Loader2 className="w-5 h-5 text-accent-agri animate-spin" />
                      </div>
                      <div className="space-y-3 flex-1 pt-3">
                        <div className="h-2 bg-white/5 rounded-full w-3/4" />
                        <div className="h-2 bg-white/5 rounded-full w-1/2" />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
            <div ref={messagesEndRef} className="h-40" />
          </div>
        </main>

        {/* Input Area */}
        <div className="absolute bottom-0 left-0 right-0 z-40 bg-gradient-to-t from-[#0c0d0c] via-[#0c0d0c]/90 to-transparent pt-20 pb-8 px-6">
          <div className="max-w-[840px] mx-auto">
            <div className="relative group">
              <form onSubmit={handleSubmit} className="relative bg-[#1a1c1a]/80 backdrop-blur-xl border border-white/5 rounded-[1.5rem] shadow-2xl focus-within:border-accent-agri/30 focus-within:ring-4 focus-within:ring-accent-agri/5 transition-all duration-500 overflow-hidden">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Analyze ROI, check subsidies, or ask about crops..."
                  rows={1}
                  className="w-full bg-transparent text-white placeholder-white/20 pl-7 pr-16 py-6 outline-none text-[15px] sm:text-[16px] resize-none max-h-48 leading-relaxed font-medium"
                  disabled={isLoading}
                />
                <div className="absolute right-4 bottom-4 flex items-center gap-2">
                  <button
                    type="submit"
                    disabled={!input.trim() || isLoading}
                    className="w-12 h-12 bg-accent-agri text-black rounded-2xl flex items-center justify-center disabled:opacity-20 disabled:grayscale hover:scale-105 active:scale-95 transition-all shadow-xl shadow-accent-agri/20"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </form>
              <div className="flex justify-center mt-4">
                <p className="text-[10px] text-white/10 font-bold uppercase tracking-[0.3em] flex items-center gap-3">
                  <span className="w-1 h-1 rounded-full bg-accent-agri/30" />
                  Verified Agricultural Intelligence
                  <span className="w-1 h-1 rounded-full bg-accent-agri/30" />
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
