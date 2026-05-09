"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2, Leaf, CloudSun, RotateCcw, Menu, X, MessageSquare, Plus } from "lucide-react";
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

const SUGGESTED_QUESTIONS = [
  "What is PM-KISAN scheme and how to apply?",
  "What is the weather in Delhi today?",
  "Best practices for wheat cultivation in Punjab?",
  "How to identify and treat late blight in potato?",
  "What is the MSP for rice in 2024?",
  "Tell me about drip irrigation benefits",
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

  // Fetch recent sessions
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
        fetchSessions(); // Refresh sidebar
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
          content: "Sorry, I encountered an error. Please check your connection and try again.",
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

  if (!isLoaded) return <div className="h-screen bg-[#212121] flex items-center justify-center"><Loader2 className="animate-spin text-white/20" /></div>;

  return (
    <div className="h-[100dvh] bg-[#212121] text-[#ececec] flex font-sans overflow-hidden">
      {/* Sidebar Overlay (Mobile) */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden" 
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`fixed lg:relative inset-y-0 left-0 w-72 bg-[#171717] border-r border-white/10 z-50 transform ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 transition-transform duration-200 ease-in-out flex flex-col`}>
        <div className="p-4">
          <button 
            onClick={startNewChat}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg border border-white/10 hover:bg-white/5 transition-colors text-sm font-medium"
          >
            <Plus className="w-4 h-4" />
            New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-2 space-y-1">
          <div className="text-[11px] font-semibold text-white/30 uppercase tracking-wider mb-2 px-3">Recent Conversations</div>
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => loadSession(s.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left text-sm transition-colors ${sessionId === s.id ? 'bg-white/10 text-white' : 'text-white/60 hover:bg-white/5 hover:text-white/80'}`}
            >
              <MessageSquare className="w-4 h-4 shrink-0" />
              <span className="truncate">{s.title}</span>
            </button>
          ))}
          {sessions.length === 0 && (
            <div className="px-3 py-4 text-xs text-white/20 italic">No previous chats yet</div>
          )}
        </div>

        <div className="p-4 border-t border-white/10">
          <div className="flex items-center justify-between px-2">
            {isSignedIn && (
              <div className="flex items-center gap-3">
                <UserButton afterSignOutUrl="/" appearance={{ elements: { userButtonAvatarBox: "w-8 h-8" } }} />
                <div className="text-xs">
                  <div className="text-white/80 font-medium">My Account</div>
                  <div className="text-white/40">Settings</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Header */}
        <header className="border-b border-white/10 bg-[#212121] px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setIsSidebarOpen(true)}
              className="lg:hidden p-1.5 hover:bg-white/5 rounded-md text-white/60"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2.5">
              <div className="bg-[#10a37f] p-1 rounded-md">
                <Leaf className="w-4 h-4 text-white" />
              </div>
              <span className="text-base font-semibold text-white/90">AgriBot</span>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            {!isSignedIn && (
              <SignInButton mode="modal">
                <button className="text-xs bg-white text-black px-3 py-1.5 rounded-md font-medium hover:bg-white/90">Sign In</button>
              </SignInButton>
            )}
            <div className="flex items-center gap-1.5 text-[10px] text-white/30 bg-white/5 px-2 py-1 rounded-full">
              <span className="w-1 h-1 rounded-full bg-[#10a37f] animate-pulse" />
              v2.5 PRO
            </div>
          </div>
        </header>

        {/* Chat Area */}
        <main className="flex-1 overflow-y-auto scrollbar-hide">
          <div className="max-w-[760px] mx-auto px-4 w-full">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center min-h-[75vh] text-center">
                <div className="w-14 h-14 bg-gradient-to-br from-[#10a37f] to-[#0d8a6a] rounded-2xl flex items-center justify-center mb-6 shadow-xl shadow-[#10a37f]/10">
                  <Leaf className="w-7 h-7 text-white" />
                </div>
                <h1 className="text-2xl font-bold mb-3 text-white/95 tracking-tight">How can I help you today?</h1>
                <p className="text-white/40 max-w-sm text-[13px] leading-relaxed mb-10">
                  Expert agricultural advice for Indian farmers. Ask about crops, weather, mandi prices, or government schemes.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl">
                  {SUGGESTED_QUESTIONS.map((q) => (
                    <button
                      key={q}
                      onClick={() => handleSubmit(undefined, q)}
                      className="text-left text-[13px] px-5 py-4 rounded-xl border border-white/10 text-white/60 hover:bg-white/5 hover:text-white/90 hover:border-white/20 transition-all group"
                    >
                      {q.includes("weather") && <CloudSun className="w-4 h-4 inline mr-2 text-yellow-400/50 group-hover:text-yellow-400" />}
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="py-8 space-y-0">
                {messages.map((msg, idx) => (
                  <div key={idx} className={`py-6 ${idx > 0 ? "border-t border-white/5" : ""}`}>
                    <div className="flex gap-5 items-start max-w-[700px] mx-auto">
                      <div className={`w-8 h-8 shrink-0 rounded-lg flex items-center justify-center ${msg.role === "user" ? "bg-white/10" : "bg-[#10a37f]"}`}>
                        {msg.role === "user" ? <User className="w-4 h-4 text-white/80" /> : <Bot className="w-4 h-4 text-white" />}
                      </div>
                      <div className="flex-1 min-w-0 pt-0.5">
                        <div className="text-[15px] leading-[1.6] text-white/90 prose prose-invert prose-sm max-w-none prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-1 prose-strong:text-white prose-hr:border-white/10">
                          {msg.role === "user" ? msg.content : <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="py-6 border-t border-white/5">
                    <div className="flex gap-5 items-start max-w-[700px] mx-auto">
                      <div className="w-8 h-8 shrink-0 rounded-lg bg-[#10a37f] flex items-center justify-center">
                        <Bot className="w-4 h-4 text-white" />
                      </div>
                      <div className="flex items-center gap-3 text-sm text-white/30 pt-1.5 font-medium italic">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Analyzing data...
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
            <div ref={messagesEndRef} className="h-32" />
          </div>
        </main>

        {/* Input Area */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-[#212121] via-[#212121] to-transparent pt-12 pb-6 px-4">
          <div className="max-w-[760px] mx-auto relative group">
            <form onSubmit={handleSubmit} className="relative bg-[#2f2f2f] border border-white/10 rounded-2xl shadow-2xl group-focus-within:border-white/20 transition-all">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask your agricultural query..."
                rows={1}
                className="w-full bg-transparent text-white placeholder-white/20 pl-6 pr-14 py-4 outline-none rounded-2xl text-[15px] resize-none max-h-32 leading-relaxed"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="absolute right-3 bottom-3 w-10 h-10 bg-white text-[#212121] rounded-xl flex items-center justify-center disabled:opacity-20 disabled:cursor-not-allowed hover:scale-105 transition-all"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
            <p className="text-center mt-3 text-[10px] text-white/20 font-medium tracking-wide">
              AgriBot Professional v2.5 • Verified Agricultural Intelligence
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
