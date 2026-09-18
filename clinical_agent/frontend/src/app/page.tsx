"use client";

import { useState, useRef, useEffect } from "react";
import { Send, User, Bot, Activity, Square, PlusCircle } from "lucide-react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type Message = {
  role: "user" | "assistant";
  content: string;
};

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const [sessionId, setSessionId] = useState<string>("");

  // Generate the random session ID only once when the page loads
  useEffect(() => {
    const uniqueId = "session_" + Math.random().toString(36).substring(2, 15);
    setSessionId(uniqueId);
    console.log("New Chat Session Started:", uniqueId);
  }, []);

  // Auto-scroll to the newest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Function to stop the generation mid-stream
  const stopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  };

  // Function to completely reset the chat and clear session memory
  const startNewChat = () => {
    stopGeneration(); // Stop if it's currently thinking
    setMessages([]); // Clear the UI
    const newId = "session_" + Math.random().toString(36).substring(2, 15);
    setSessionId(newId); // Give LangGraph a clean slate!
    console.log("Started a completely new chat session:", newId);
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    // Initialize the AbortController for this specific request
    abortControllerRef.current = new AbortController();

    try {
      const apiUrl = "https://clinical-backend.victoriousbush-7b0515a9.westus2.azurecontainerapps.io";
      
      const res = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          prompt: userMessage,
          session_id: sessionId 
        }),
        signal: abortControllerRef.current.signal 
      });

      if (!res.body) throw new Error("No response body");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let streamedText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        streamedText += decoder.decode(value, { stream: true });
        
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1].content = streamedText;
          return updated;
        });
      }
    } catch (error: any) {
      if (error.name === 'AbortError') {
        // Handle manual cancellation cleanly
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1].content += "\n\n*(Generation stopped by user)*";
          return updated;
        });
      } else {
        console.error("Chat Error:", error);
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1].content = "Error connecting to clinical backend.";
          return updated;
        });
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-50 font-sans">
      {/* Header */}
      <header className="bg-blue-900 text-white p-4 shadow-md flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Activity className="w-6 h-6 text-blue-300" />
          <h1 className="text-xl font-bold tracking-wide">MIMIC-IV Clinical Agent</h1>
        </div>
        
        <button
          onClick={startNewChat}
          className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium bg-blue-800 hover:bg-blue-700 rounded-lg border border-blue-700 transition-colors shadow-sm"
        >
          <PlusCircle size={16} />
          New Chat
        </button>
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto p-4 sm:p-6 md:p-8 flex flex-col gap-6">
        {messages.length === 0 && (
          <div className="text-center text-slate-400 mt-20">
            <Bot className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p className="text-lg text-slate-600 font-medium">Ready to query patient records.</p>
            <p className="text-sm mt-2">Try asking for a patient's latest labs, charts, or a CSV export.</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-4 max-w-4xl mx-auto w-full ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
            <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-sm ${msg.role === "user" ? "bg-blue-600 text-white" : "bg-emerald-600 text-white"}`}>
              {msg.role === "user" ? <User size={20} /> : <Bot size={20} />}
            </div>
            
            <div className={`p-4 rounded-2xl shadow-sm text-slate-800 ${msg.role === "user" ? "bg-blue-100 rounded-tr-none" : "bg-white rounded-tl-none border border-slate-200 overflow-x-auto w-full"}`}>
              {msg.role === "user" ? (
                <div className="whitespace-pre-wrap">{msg.content}</div>
              ) : (
                <div className="flex flex-col h-full">
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    className="prose prose-slate max-w-none w-full"
                  >
                    {msg.content}
                  </ReactMarkdown>
                  
                  {/* Thinking UI with Stop Button */}
                  {isLoading && idx === messages.length - 1 && (
                    <div className="flex items-center justify-between mt-4 p-3 bg-slate-50 border border-slate-200 rounded-lg shadow-sm">
                      <div className="flex items-center gap-3">
                        <div className="flex gap-1.5">
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                        </div>
                        <span className="text-sm text-slate-600 font-medium">Agent is thinking...</span>
                      </div>
                      
                      <button
                        onClick={stopGeneration}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-600 bg-white border border-slate-300 rounded-md hover:bg-red-50 hover:text-red-600 hover:border-red-300 transition-all shadow-sm"
                      >
                        <Square size={12} fill="currentColor" />
                        Stop
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </main>

      {/* Input Area */}
      <footer className="bg-white p-4 border-t border-slate-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]">
        <div className="max-w-4xl mx-auto relative flex items-center">
          <input
            type="text"
            className="w-full pl-4 pr-12 py-4 text-slate-900 placeholder:text-slate-400 bg-slate-100 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all outline-none"
            placeholder="Search for a patient..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="absolute right-2 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600 transition-colors"
          >
            <Send size={20} />
          </button>
        </div>
      </footer>
    </div>
  );
}