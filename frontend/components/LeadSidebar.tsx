"use client";

import type { Analytics, LeadSlots } from "@/lib/api";

interface LeadSidebarProps {
  slots: LeadSlots;
  analytics?: Analytics | null;
  ended: boolean;
  bookingMode: "success" | "fail";
  onBookingModeChange: (mode: "success" | "fail") => void;
}

function SlotField({
  label,
  value,
  highlight,
}: {
  label: string;
  value?: string | null;
  highlight?: boolean;
}) {
  return (
    <div className="py-2">
      <p className="text-[10px] uppercase tracking-widest text-cream/40">{label}</p>
      <p
        className={`text-sm mt-0.5 ${
          highlight ? "text-champagne" : value ? "text-cream" : "text-cream/30"
        }`}
      >
        {value || "—"}
      </p>
    </div>
  );
}

function InterestBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    high: "bg-forest/40 text-green-300",
    medium: "bg-champagne/20 text-champagne",
    low: "bg-cream/10 text-cream/60",
    not_interested: "bg-red-900/30 text-red-300",
    unknown: "bg-cream/5 text-cream/40",
  };
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wider ${
        colors[level] || colors.unknown
      }`}
    >
      {level.replace("_", " ")}
    </span>
  );
}

export function LeadSidebar({
  slots,
  analytics,
  ended,
  bookingMode,
  onBookingModeChange,
}: LeadSidebarProps) {
  const data = ended && analytics ? analytics : null;
  const visitStatus = data?.site_visit_status ?? slots.site_visit_status;

  return (
    <aside className="flex h-full flex-col border-l border-cream/10 bg-ink/80">
      <div className="border-b border-cream/10 px-5 py-4">
        <h2 className="font-display text-lg text-cream">
          {ended ? "Lead Dossier" : "Lead Intelligence"}
        </h2>
        <p className="text-xs text-cream/40 mt-0.5">
          {ended ? "Post-conversation analytics" : "Live qualification"}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin px-5 py-3">
        {data?.lead_summary && (
          <div className="mb-4 rounded-lg bg-cream/5 p-3">
            <p className="text-[10px] uppercase tracking-widest text-cream/40 mb-1">
              Summary
            </p>
            <p className="text-sm text-cream/80 leading-relaxed">
              {data.lead_summary}
            </p>
          </div>
        )}

        <SlotField
          label="Configuration"
          value={data?.configuration ?? slots.configuration}
        />
        <SlotField label="Budget" value={data?.budget ?? slots.budget} />
        <SlotField
          label="Budget Fit"
          value={data?.budget_fit ?? slots.budget_fit}
        />
        <SlotField label="Timeline" value={data?.timeline ?? slots.timeline} />

        <div className="py-2">
          <p className="text-[10px] uppercase tracking-widest text-cream/40">
            Interest Level
          </p>
          <div className="mt-1">
            <InterestBadge
              level={data?.interest_level ?? slots.interest_level}
            />
          </div>
        </div>

        <SlotField
          label="Site Visit"
          value={visitStatus.replace("_", " ")}
          highlight={visitStatus === "confirmed"}
        />
        {(slots.site_visit_details.date || slots.site_visit_details.time) && (
          <SlotField
            label="Visit Time"
            value={[
              slots.site_visit_details.date,
              slots.site_visit_details.time,
            ]
              .filter(Boolean)
              .join(" · ")}
          />
        )}

        <SlotField
          label="Follow-up"
          value={
            (data?.follow_up_required ?? slots.follow_up.needed)
              ? data?.follow_up_time ?? slots.follow_up.when ?? "Yes"
              : "No"
          }
        />

        {(data?.objections_raised?.length || slots.objections.length) > 0 && (
          <div className="py-2">
            <p className="text-[10px] uppercase tracking-widest text-cream/40">
              Objections
            </p>
            <div className="mt-1 flex flex-wrap gap-1">
              {(data?.objections_raised ?? slots.objections).map((o) => (
                <span
                  key={o}
                  className="rounded bg-cream/10 px-2 py-0.5 text-xs text-cream/70"
                >
                  {o}
                </span>
              ))}
            </div>
          </div>
        )}

        {(slots.opt_out || data?.opt_out) && (
          <div className="mt-2 rounded bg-red-900/20 px-3 py-2 text-xs text-red-300">
            Customer opted out
          </div>
        )}

        {(slots.escalated_to_human || data?.escalated_to_human) && (
          <div className="mt-2 rounded bg-champagne/10 px-3 py-2 text-xs text-champagne">
            Escalated to human
          </div>
        )}

        {data?.conversation_outcome && (
          <SlotField label="Outcome" value={data.conversation_outcome} />
        )}
        {data?.confidence_notes && (
          <SlotField label="Notes" value={data.confidence_notes} />
        )}
      </div>

      {!ended && (
        <div className="border-t border-cream/10 px-5 py-3">
          <p className="text-[10px] uppercase tracking-widest text-cream/40 mb-2">
            Demo: Booking Mode
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => onBookingModeChange("success")}
              className={`flex-1 rounded-lg py-1.5 text-xs transition ${
                bookingMode === "success"
                  ? "bg-forest text-cream"
                  : "bg-cream/10 text-cream/60 hover:bg-cream/20"
              }`}
            >
              Success
            </button>
            <button
              type="button"
              onClick={() => onBookingModeChange("fail")}
              className={`flex-1 rounded-lg py-1.5 text-xs transition ${
                bookingMode === "fail"
                  ? "bg-red-800 text-cream"
                  : "bg-cream/10 text-cream/60 hover:bg-cream/20"
              }`}
            >
              Fail
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}
