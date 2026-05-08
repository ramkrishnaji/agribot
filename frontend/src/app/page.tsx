"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2, Leaf, CloudSun, RotateCcw } from "lucide-react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
  role: "user" | "bot";
  content: string;
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
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Auto-resize textarea
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
          content:
            "Sorry, I encountered an error connecting to the server. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setSessionId(null);
  };

  return (
    <div className="h-[100dvh] bg-[#212121] text-[#ececec] flex flex-col font-sans">
      {/* Header */}
      <header className="border-b border-white/10 bg-[#212121] sticky top-0 z-10 px-4 py-3">
        <div className="max-w-[760px] mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="bg-[#10a37f] p-1.5 rounded-lg">
              <Leaf className="w-4 h-4 text-white" />
            </div>
            <span className="text-base font-medium text-white/90">AgriBot</span>
            <span className="text-xs text-white/40 ml-1 hidden sm:inline">
              Indian Agriculture Assistant
            </span>
          </div>
          <div className="flex items-center gap-3">
            {messages.length > 0 && (
              <button
                onClick={clearChat}
                title="Clear chat"
                className="flex items-center gap-1.5 text-xs text-white/40 hover:text-white/70 transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">New chat</span>
              </button>
            )}
            <div className="flex items-center gap-1.5 text-xs text-white/40">
              <span className="w-1.5 h-1.5 rounded-full bg-[#10a37f] animate-pulse" />
              Online
            </div>
          </div>
        </div>
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-[760px] mx-auto px-4">
          {messages.length === 0 ? (
            /* Welcome screen */
            <div className="flex flex-col items-center justify-center min-h-[70vh] text-center pt-16">
              <div className="w-16 h-16 bg-gradient-to-br from-[#10a37f] to-[#0d8a6a] rounded-2xl flex items-center justify-center mb-5 shadow-lg shadow-[#10a37f]/20">
                <Leaf className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-2xl font-semibold mb-2 text-white/90">
                Kisan Saathi — AgriBot
              </h1>
              <p className="text-white/40 max-w-md text-sm leading-relaxed mb-8">
                Ask me anything about Indian agriculture — crops, soil, government
                schemes, weather, pest management, and more. Available in Hindi too.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full max-w-lg">
                {SUGGESTED_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSubmit(undefined, q)}
                    className="text-left text-sm px-4 py-3 rounded-xl border border-white/10 text-white/60 hover:bg-white/5 hover:text-white/80 hover:border-white/20 transition-all duration-150"
                  >
                    {q.includes("weather") && (
                      <CloudSun className="w-3.5 h-3.5 inline mr-1.5 text-yellow-400/70" />
                    )}
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Messages */
            <div className="py-6 space-y-0">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`py-5 ${idx > 0 ? "border-t border-white/5" : ""}`}
                >
                  <div className="flex gap-4 items-start">
                    {/* Avatar */}
                    <div
                      className={`w-7 h-7 shrink-0 rounded-full flex items-center justify-center ${
                        msg.role === "user"
                          ? "bg-[#5436DA]"
                          : "bg-[#10a37f]"
                      }`}
                    >
                      {msg.role === "user" ? (
                        <User className="w-3.5 h-3.5 text-white" />
                      ) : (
                        <Bot className="w-3.5 h-3.5 text-white" />
                      )}
                    </div>

                    {/* Message content */}
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-medium text-white/50 mb-1.5">
                        {msg.role === "user" ? "You" : "AgriBot"}
                      </div>

                      {msg.role === "user" ? (
                        <div className="text-[15px] leading-relaxed text-white/85 whitespace-pre-wrap">
                          {msg.content}
                        </div>
                      ) : (
                        /* Render bot responses as markdown */
                        <div className="text-[15px] leading-relaxed text-white/85 prose prose-invert prose-sm max-w-none
                          prose-p:my-1.5 prose-p:leading-relaxed
                          prose-ul:my-1.5 prose-ul:pl-4
                          prose-ol:my-1.5 prose-ol:pl-4
                          prose-li:my-0.5 prose-li:leading-relaxed
                          prose-strong:text-white/95 prose-strong:font-semibold
                          prose-h1:text-white/90 prose-h1:text-lg prose-h1:font-semibold prose-h1:mt-3 prose-h1:mb-1.5
                          prose-h2:text-white/90 prose-h2:text-base prose-h2:font-semibold prose-h2:mt-3 prose-h2:mb-1.5
                          prose-h3:text-white/85 prose-h3:text-sm prose-h3:font-medium prose-h3:mt-2 prose-h3:mb-1
                          prose-code:text-[#10a37f] prose-code:bg-white/5 prose-code:px-1 prose-code:rounded prose-code:text-sm
                          prose-blockquote:border-l-2 prose-blockquote:border-[#10a37f]/50 prose-blockquote:pl-3 prose-blockquote:text-white/60
                          prose-hr:border-white/10">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.content}
                          </ReactMarkdown>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {/* Loading indicator */}
              {isLoading && (
                <div className="py-5 border-t border-white/5">
                  <div className="flex gap-4 items-start">
                    <div className="w-7 h-7 shrink-0 rounded-full bg-[#10a37f] flex items-center justify-center">
                      <Bot className="w-3.5 h-3.5 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="text-xs font-medium text-white/50 mb-1.5">
                        AgriBot
                      </div>
                      <div className="flex items-center gap-2 text-sm text-white/40">
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        Thinking...
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Area */}
      <footer className="pb-4 pt-2 px-4">
        <div className="max-w-[760px] mx-auto">
          <form
            onSubmit={handleSubmit}
            className="relative bg-[#2f2f2f] border border-white/10 rounded-2xl shadow-lg focus-within:border-white/20 transition-colors"
          >
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message AgriBot... (Shift+Enter for new line)"
              rows={1}
              className="w-full bg-transparent text-white placeholder-white/30 pl-5 pr-14 py-3.5 outline-none rounded-2xl text-[15px] resize-none max-h-32 leading-relaxed"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="absolute right-2 bottom-2 w-8 h-8 bg-white text-[#212121] rounded-lg flex items-center justify-center disabled:opacity-30 disabled:cursor-not-allowed hover:bg-white/90 transition-colors"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
          <p className="text-center mt-2 text-[11px] text-white/25">
            AgriBot uses Gemini + RAG. Answers are grounded in verified Indian agriculture data.
          </p>
        </div>
      </footer>
    </div>
  );
}
