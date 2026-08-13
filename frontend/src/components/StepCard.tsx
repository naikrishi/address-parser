import type { PipelineStep, PipelineStepStatus } from "../types";

interface StepCardProps {
  step: PipelineStep;
}

const STATUS_STYLES: Record<PipelineStepStatus, string> = {
  complete: "bg-emerald-100/85 text-emerald-900",
  in_progress: "bg-amber-100/85 text-amber-900",
  error: "bg-rose-100/85 text-rose-900",
  pending: "bg-blue-100/85 text-blue-900",
  skipped: "bg-zinc-100/85 text-zinc-700",
};

const STATUS_LABELS: Record<PipelineStepStatus, string> = {
  complete: "Complete",
  in_progress: "In Progress",
  error: "Error",
  pending: "Pending",
  skipped: "Skipped",
};

export function StepCard({ step }: StepCardProps) {
  const statusClass = STATUS_STYLES[step.status] ?? STATUS_STYLES.pending;
  const statusLabel = STATUS_LABELS[step.status] ?? STATUS_LABELS.pending;
  const detailEntries = Object.entries(step.details ?? {});

  return (
    <article className="panel p-4 sm:p-5">
      <header className="mb-3 flex items-start justify-between gap-2">
        <div>
          <p className="kicker">
            Step {step.id}
          </p>
          <h2 className="headline text-xl font-bold">{step.title}</h2>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-xs font-semibold ${statusClass}`}
        >
          {statusLabel}
        </span>
      </header>

      <p className="subcopy text-sm">{step.summary}</p>

      {detailEntries.length > 0 && (
        <dl className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {detailEntries.map(([key, value]) => (
            <div key={key} className="rounded-lg border border-[rgba(13,44,114,0.14)] bg-white/65 px-3 py-2">
              <dt className="kicker">{key}</dt>
              <dd className="text-sm font-semibold text-[var(--text-primary)]">
                {value === null ? "N/A" : String(value)}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </article>
  );
}
