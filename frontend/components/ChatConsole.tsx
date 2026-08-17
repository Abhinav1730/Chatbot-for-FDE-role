"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  createSession,
  sendMessage,
  endSession,
  updateBookingMode,
  type LeadSlots,
  type Analytics,
  type BookingResult,
} from "@/lib/api";
import { MessageBubble } from "./MessageBubble";
import { LeadSidebar } from "./LeadSidebar";
import { SuggestionChips } from "./SuggestionChips";
import { BookingCard } from "./BookingCard";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
}

export function ChatConsole() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [slots, setSlots] = useState<LeadSlots | null>(null);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [ended, setEnded] = useState(false);
  const [bookingMode, setBookingMode] = useState<"success" | "fail">("success");
  const [lastBooking, setLastBooking] = useState<BookingResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    async function init() {
      try {
        const data = await createSession();
        setSessionId(data.session_id);
        setSlots(data.slots);
        setMessages([
          {
            role: "assistant",
            content: data.greeting,
            timestamp: new Date().toISOString(),
          },
        ]);
      } catch {
        setError("Could not connect to server. Is the backend running on port 8000?");
      } finally {
        setInitializing(false);
      }
    }
    init();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = useCallback(
    async (text: string) => {
      if (!sessionId || !text.trim() || loading || ended) return;

      const userMsg: ChatMessage = {
        role: "user",
        content: text.trim(),
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setLoading(true);
      setError(null);

      try {
        const data = await sendMessage(sessionId, text.trim());
        setSlots(data.slots);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: data.reply,
            timestamp: new Date().toISOString(),
          },
        ]);
        if (data.booking) {
          setLastBooking(data.booking);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to send message");
      } finally {
        setLoading(false);
        inputRef.current?.focus();
      }
    },
    [sessionId, loading, ended]
  );

  const handleEnd = async () => {
    if (!sessionId || ended) return;
    setLoading(true);
    try {
      const data = await endSession(sessionId);
      setAnalytics(data.analytics);
      setEnded(true);
    } catch {
      setError("Failed to generate analytics");
    } finally {
      setLoading(false);
    }
  };

  const handleBookingModeChange = async (mode: "success" | "fail") => {
    setBookingMode(mode);
    if (sessionId) {
      try {
        await updateBookingMode(sessionId, mode);
      } catch {
        /* ignore */
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend(input);
    }
  };

  if (initializing) {
    return (
      <div className="flex h-screen items-center justify-center bg-ink">
        <motion.div
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ repeat: Infinity, duration: 1.5 }}
          className="font-display text-xl text-champagne"
        >
          Northstar Homes
        </motion.div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-ink">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-cream/10 px-6 py-4">
        <div>
          <h1 className="font-display text-2xl text-cream tracking-tight">
            Northstar Homes
          </h1>
          <p className="text-xs text-cream/50 mt-0.5">
            Project Northstar One · Sector 79, Gurugram
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span
              className={`h-2 w-2 rounded-full ${
                error ? "bg-red-400" : ended ? "bg-cream/30" : "bg-green-400"
              }`}
            />
            <span className="text-xs text-cream/50">
              {error ? "Disconnected" : ended ? "Ended" : "Live"}
            </span>
          </div>
          {!ended && (
            <button
              type="button"
              onClick={handleEnd}
              disabled={loading}
              className="rounded-lg border border-cream/20 px-4 py-1.5 text-xs text-cream/70 transition hover:border-champagne hover:text-champagne disabled:opacity-40"
            >
              End Conversation
            </button>
          )}
        </div>
      </header>

      {/* Main body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Chat column */}
        <div className="flex flex-1 flex-col bg-cream">
          {/* Empty state project card */}
          {messages.length <= 1 && !ended && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mx-auto mt-6 max-w-lg rounded-2xl border border-stone bg-white/60 p-6 shadow-sm"
            >
              <h3 className="font-display text-lg text-ink">Project Northstar One</h3>
              <p className="text-sm text-ink/60 mt-1">Sector 79, Gurugram</p>
              <div className="mt-4 grid grid-cols-2 gap-3">
                <div className="rounded-xl bg-stone/50 p-3">
                  <p className="text-xs text-ink/50">2 BHK</p>
                  <p className="font-display text-sm text-ink mt-0.5">
                    ₹1.35 Cr onwards
                  </p>
                </div>
                <div className="rounded-xl bg-stone/50 p-3">
                  <p className="text-xs text-ink/50">3 BHK</p>
                  <p className="font-display text-sm text-ink mt-0.5">
                    ₹1.75 Cr onwards
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto scrollbar-thin px-6 py-4 space-y-4">
            <AnimatePresence>
              {messages.map((msg, i) => (
                <MessageBubble
                  key={i}
                  role={msg.role}
                  content={msg.content}
                  timestamp={msg.timestamp}
                />
              ))}
            </AnimatePresence>

            {lastBooking && (
              <BookingCard
                status={lastBooking.status}
                date={slots?.site_visit_details.date}
                time={slots?.site_visit_details.time}
                message={lastBooking.message}
              />
            )}

            {loading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex justify-start"
              >
                <div className="rounded-2xl rounded-bl-md bg-stone/90 px-4 py-3">
                  <div className="flex gap-1">
                    {[0, 1, 2].map((i) => (
                      <motion.span
                        key={i}
                        className="h-2 w-2 rounded-full bg-ink/30"
                        animate={{ opacity: [0.3, 1, 0.3] }}
                        transition={{
                          repeat: Infinity,
                          duration: 1,
                          delay: i * 0.2,
                        }}
                      />
                    ))}
                  </div>
                </div>
              </motion.div>
            )}

            {error && (
              <p className="text-center text-xs text-red-600">{error}</p>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Composer */}
          {!ended && (
            <div className="border-t border-stone bg-cream/80">
              <SuggestionChips
                onSelect={handleSend}
                disabled={loading}
              />
              <div className="flex items-center gap-3 px-4 pb-4">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={loading}
                  placeholder="Type in English, Hindi, or Hinglish..."
                  className="flex-1 rounded-2xl border border-stone bg-white px-5 py-3 text-sm text-ink placeholder:text-ink/30 focus:border-champagne focus:outline-none focus:ring-1 focus:ring-champagne/30 disabled:opacity-50"
                />
                <button
                  type="button"
                  onClick={() => handleSend(input)}
                  disabled={loading || !input.trim()}
                  className="rounded-2xl bg-forest px-5 py-3 text-sm font-medium text-cream transition hover:bg-forest/90 disabled:opacity-40"
                >
                  Send
                </button>
              </div>
            </div>
          )}

          {ended && (
            <div className="border-t border-stone bg-cream/80 px-6 py-4 text-center">
              <p className="text-sm text-ink/60">
                Conversation ended. Review the lead dossier on the right.
              </p>
            </div>
          )}
        </div>

        {/* Sidebar */}
        {slots && (
          <div className="w-80 shrink-0">
            <LeadSidebar
              slots={slots}
              analytics={analytics}
              ended={ended}
              bookingMode={bookingMode}
              onBookingModeChange={handleBookingModeChange}
            />
          </div>
        )}
      </div>
    </div>
  );
}
