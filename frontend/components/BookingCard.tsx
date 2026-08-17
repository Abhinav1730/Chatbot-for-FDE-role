"use client";

import { motion } from "framer-motion";

interface BookingCardProps {
  status: string;
  date?: string | null;
  time?: string | null;
  message?: string | null;
}

export function BookingCard({ status, date, time, message }: BookingCardProps) {
  const isConfirmed = status === "confirmed";
  const isFailed = status === "failed";

  if (!isConfirmed && !isFailed) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`mx-auto max-w-sm rounded-xl border p-4 ${
        isConfirmed
          ? "border-forest/30 bg-forest/10"
          : "border-red-400/30 bg-red-50/10"
      }`}
    >
      <div className="flex items-center gap-2 mb-2">
        <span
          className={`text-xs font-medium uppercase tracking-wider ${
            isConfirmed ? "text-forest" : "text-red-600"
          }`}
        >
          {isConfirmed ? "Visit Confirmed" : "Booking Failed"}
        </span>
      </div>
      {(date || time) && (
        <p className="text-sm text-ink/80">
          {date && <span>{date}</span>}
          {date && time && <span> · </span>}
          {time && <span>{time}</span>}
        </p>
      )}
      {message && (
        <p className="mt-1 text-xs text-ink/50">{message}</p>
      )}
    </motion.div>
  );
}
