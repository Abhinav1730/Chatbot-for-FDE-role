"use client";

interface SuggestionChipsProps {
  onSelect: (text: string) => void;
  disabled?: boolean;
}

const SUGGESTIONS = [
  { label: "2BHK kitna hai?", text: "2BHK ka price kya hai?" },
  { label: "I'm interested in 3 BHK", text: "I'm interested in a 3 BHK apartment" },
  { label: "Bahut costly lagta hai", text: "Bahut expensive lag raha hai, costly hai" },
  { label: "Book site visit", text: "I'd like to book a site visit this Saturday at 11 AM" },
];

export function SuggestionChips({ onSelect, disabled }: SuggestionChipsProps) {
  return (
    <div className="flex flex-wrap gap-2 px-4 pb-2">
      {SUGGESTIONS.map((s) => (
        <button
          key={s.label}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(s.text)}
          className="rounded-full border border-champagne/30 bg-cream/50 px-3 py-1.5 text-xs text-ink/70 transition hover:border-champagne hover:bg-champagne/10 hover:text-ink disabled:opacity-40"
        >
          {s.label}
        </button>
      ))}
    </div>
  );
}
