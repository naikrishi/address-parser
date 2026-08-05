import type { PipelineStep, PipelineStepStatus } from "../types";

interface StepCardProps {
  step: PipelineStep;
}

const STATUS_STYLES: Record<PipelineStepStatus, string> = {
  complete: "bg-emerald-100 text-emerald-800",
  in_progress: "bg-amber-100 text-amber-800",
  pending: "bg-slate-100 text-slate-800",
  skipped: "bg-zinc-100 text-zinc-600",
};

const STATUS_LABELS: Record<PipelineStepStatus, string> = {
  complete: "Complete",
  in_progress: "In Progress",
  pending: "Pending",
  skipped: "Skipped",
};

export function StepCard({ step }: StepCardProps) {
  const statusClass = STATUS_STYLES[step.status] ?? STATUS_STYLES.pending;
  const statusLabel = STATUS_LABELS[step.status] ?? STATUS_LABELS.pending;
  const detailEntries = Object.entries(step.details ?? {});

  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <header className="mb-3 flex items-start justify-between gap-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Step {step.id}
          </p>
          <h2 className="text-lg font-semibold text-slate-900">{step.title}</h2>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-xs font-semibold ${statusClass}`}
        >
          {statusLabel}
        </span>
      </header>

      <p className="text-sm text-slate-700">{step.summary}</p>

      {detailEntries.length > 0 && (
        <dl className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {detailEntries.map(([key, value]) => (
            <div key={key} className="rounded-md bg-slate-50 px-3 py-2">
              <dt className="text-xs font-medium uppercase text-slate-500">{key}</dt>
              <dd className="text-sm font-medium text-slate-800">
                {value === null ? "N/A" : String(value)}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </article>
  );
}
