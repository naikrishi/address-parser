import { Link, useParams } from "react-router-dom";
import { ApiError } from "../api";
import { StepCard } from "../components";
import { useParseDetail } from "../hooks";
import type {
	EnrichmentResultResponse,
	GeocodePayloadBusiness,
	GeocodeResultResponse,
	PipelineStep,
} from "../types";

const CONFIDENCE_COLOR: Record<string, string> = {
	high: "bg-emerald-100 text-emerald-800",
	medium: "bg-amber-100 text-amber-800",
	low: "bg-rose-100 text-rose-800",
};

function toConfidenceLabel(score: number | null): "high" | "medium" | "low" | null {
	if (score === null) return null;
	if (score >= 0.7) return "high";
	if (score >= 0.4) return "medium";
	return "low";
}

function toBusinessList(geocode: GeocodeResultResponse | undefined): GeocodePayloadBusiness[] {
	if (!geocode) {
		return [];
	}
	const raw = geocode.result_payload?.nearby_businesses;
	if (!Array.isArray(raw)) {
		return [];
	}
	return raw.filter((item): item is GeocodePayloadBusiness => Boolean(item && typeof item === "object"));
}

function latestByDate<T extends { created_at: string }>(rows: T[]): T | undefined {
	return [...rows].sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at))[0];
}

function toStatus(value: string): PipelineStep["status"] {
	if (value === "complete") {
		return "complete";
	}
	if (value === "partial") {
		return "in_progress";
	}
	if (value === "error") {
		return "error";
	}
	return "skipped";
}

function buildSteps(
	latestEnrichment: EnrichmentResultResponse | undefined,
	latestGeocode: GeocodeResultResponse | undefined,
): PipelineStep[] {
	return [
		{
			id: 1,
			title: "Libpostal Parse",
			status: "complete",
			summary: "Base parse completed when record was created.",
			details: {},
		},
		{
			id: 2,
			title: "LLM Extraction",
			status: latestEnrichment ? toStatus(latestEnrichment.status) : "pending",
			summary: latestEnrichment
				? `Provider: ${latestEnrichment.provider_name}`
				: "No enrichment result yet.",
			details: latestEnrichment?.enriched_components ?? {},
		},
		{
			id: 3,
			title: "Search Fallback Step",
			status: latestEnrichment ? "complete" : "pending",
			summary: latestEnrichment
				? "Search-assisted gap filling was considered during enrichment."
				: "Search step has not run yet.",
			details: {},
		},
		{
			id: 4,
			title: "Geocode + Nearby Businesses",
			status: latestGeocode ? toStatus(latestGeocode.status) : "pending",
			summary: latestGeocode
				? `Provider: ${latestGeocode.provider_name}`
				: "No geocode result yet.",
			details: {
				latitude: latestGeocode?.latitude ?? null,
				longitude: latestGeocode?.longitude ?? null,
			},
		},
	];
}

export function DetailPage() {
	const { parseId = "" } = useParams();
	const { data, isLoading, isError, error, refetch, isFetching } = useParseDetail(parseId);

	if (!parseId) {
		return (
			<main className="page-shell px-4 sm:px-6 lg:px-8">
				<div className="mx-auto max-w-4xl panel border-rose-200 bg-rose-50/85 p-8 text-rose-800">
					<p className="font-semibold">Missing parse id in route.</p>
					<Link to="/" className="mt-4 inline-block text-sm font-semibold text-[var(--text-primary)] underline">
						Back to pipeline
					</Link>
				</div>
			</main>
		);
	}

	if (isLoading) {
		return (
			<main className="page-shell px-4 sm:px-6 lg:px-8">
				<div className="mx-auto max-w-5xl space-y-4">
					{Array.from({ length: 4 }).map((_, i) => (
						<div key={i} className="panel animate-pulse p-5">
							<div className="h-5 w-40 rounded bg-slate-200" />
							<div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
								{Array.from({ length: 4 }).map((_, j) => (
									<div key={j}>
										<div className="h-3 w-20 rounded bg-slate-200" />
										<div className="mt-1 h-4 w-24 rounded bg-slate-200" />
									</div>
								))}
							</div>
						</div>
					))}
				</div>
			</main>
		);
	}

	if (isError || !data) {
		const status = error instanceof ApiError ? error.status : null;
		const message =
			status === 404
				? "Parse record not found. It may have been deleted or the link is stale."
				: status === 401 || status === 403
					? "Your session has expired or you do not have access to this record."
					: error instanceof Error
						? error.message
						: "Unknown error";
		return (
			<main className="page-shell px-4 sm:px-6 lg:px-8">
				<div className="mx-auto max-w-4xl panel border-rose-200 bg-rose-50/85 p-8 text-center text-rose-800">
					<p className="font-semibold">Could not load parse detail.</p>
					<p className="mt-2 text-sm">{message}</p>
					<button
						type="button"
						onClick={() => void refetch()}
						className="mt-4 rounded-md bg-rose-600 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-700"
					>
						Retry
					</button>
				</div>
			</main>
		);
	}

	const latestEnrichment = latestByDate(data.enrichment_results);
	const latestGeocode = latestByDate(data.geocode_results);
	const nearbyBusinesses = toBusinessList(latestGeocode);
	const steps = buildSteps(latestEnrichment, latestGeocode);

	return (
		<main className="page-shell px-4 sm:px-6 lg:px-8">
			<div className="mx-auto max-w-5xl">
				<header className="mb-8 reveal-sequence">
					<p className="kicker">Address Pipeline</p>
					<h1 className="headline mt-2 text-4xl font-bold sm:text-5xl">Detail View</h1>
					<p className="subcopy mt-3 text-base">
						See the input, parsed fields, enrichment result, geocode, and nearby businesses.
					</p>
					<div className="mt-4 flex items-center gap-4 text-sm">
						<Link to="/" className="font-semibold text-[var(--text-primary)] underline">
							Back to pipeline
						</Link>
						{isFetching ? <span className="text-[var(--text-secondary)]">Refreshing...</span> : null}
					</div>
				</header>

				<section className="mb-6 panel p-5 reveal-sequence sm:p-6">
					<h2 className="headline text-2xl font-bold">Raw Input</h2>
					<p className="mt-2 break-words text-[var(--text-primary)]">{data.raw_input.raw_address}</p>
					<dl className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
						<div>
							<dt className="kicker">Input Source</dt>
							<dd className="font-semibold text-[var(--text-primary)]">{data.raw_input.input_source}</dd>
						</div>
						<div>
							<dt className="kicker">Country Hint</dt>
							<dd className="font-semibold text-[var(--text-primary)]">{data.raw_input.country_hint ?? "N/A"}</dd>
						</div>
						<div>
							<dt className="kicker">Parser</dt>
							<dd className="font-semibold text-[var(--text-primary)]">{data.parser_name}</dd>
						</div>
						<div>
							<dt className="kicker">Parse Confidence</dt>
						<dd className="font-semibold text-[var(--text-primary)]">{(data.confidence_score * 100).toFixed(0)}%</dd>
						</div>
					</dl>
				</section>

				{latestEnrichment && (
					<section className="mb-6 panel p-5 reveal-sequence sm:p-6">
						<div className="flex flex-wrap items-center justify-between gap-3">
							<h2 className="headline text-2xl font-bold">Enrichment Summary</h2>
							{(() => {
								const label = toConfidenceLabel(latestEnrichment.confidence_score);
								return label ? (
									<span className={`rounded-full px-3 py-1 text-xs font-semibold capitalize ${CONFIDENCE_COLOR[label]}`}>
										{label} confidence
									</span>
								) : null;
							})()}
						</div>
						<dl className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
							<div>
								<dt className="kicker">Provider</dt>
								<dd className="font-semibold text-[var(--text-primary)]">{latestEnrichment.provider_name}</dd>
							</div>
							<div>
								<dt className="kicker">Status</dt>
								<dd className="font-semibold capitalize text-[var(--text-primary)]">{latestEnrichment.status}</dd>
							</div>
							<div>
								<dt className="kicker">Complete</dt>
								<dd className="font-semibold text-[var(--text-primary)]">{latestEnrichment.is_complete ? "Yes" : "No"}</dd>
							</div>
						</dl>
						{latestEnrichment.error_message ? (
							<p className="mt-3 rounded-md bg-rose-50 px-3 py-2 text-xs text-rose-700">{latestEnrichment.error_message}</p>
						) : null}
					</section>
				)}

				{latestGeocode && (latestGeocode.latitude !== null || latestGeocode.longitude !== null) && (
					<section className="mb-6 panel p-5 reveal-sequence sm:p-6">
						<h2 className="headline text-2xl font-bold">Geocode Coordinates</h2>
						<dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
							<div>
								<dt className="kicker">Latitude</dt>
								<dd className="font-semibold tabular-nums text-[var(--text-primary)]">{latestGeocode.latitude ?? "N/A"}</dd>
							</div>
							<div>
								<dt className="kicker">Longitude</dt>
								<dd className="font-semibold tabular-nums text-[var(--text-primary)]">{latestGeocode.longitude ?? "N/A"}</dd>
							</div>
						</dl>
					</section>
				)}

				<section className="mb-6 panel p-5 reveal-sequence sm:p-6">
					<h2 className="headline text-2xl font-bold">Parsed Components</h2>
					<dl className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
						{Object.entries(data.parsed_components).map(([key, value]) => (
							<div key={key} className="rounded-lg border border-[rgba(13,44,114,0.14)] bg-white/65 px-3 py-2">
								<dt className="kicker">{key}</dt>
								<dd className="text-sm font-semibold text-[var(--text-primary)]">{value ?? "N/A"}</dd>
							</div>
						))}
					</dl>
				</section>

				<section className="mb-6 grid gap-4">
					{steps.map((step) => (
						<StepCard key={step.id} step={step} />
					))}
				</section>

				<section className="panel p-5 reveal-sequence sm:p-6">
					<h2 className="headline text-2xl font-bold">Nearby Businesses</h2>
					{nearbyBusinesses.length === 0 ? (
						<div className="mt-4 rounded-lg border border-dashed border-[rgba(13,44,114,0.2)] py-6 text-center">
							<p className="text-sm text-[var(--text-secondary)]">No nearby businesses were returned by the geocoder.</p>
							<p className="mt-1 text-xs text-[var(--text-secondary)]">This can happen in test or stub mode.</p>
						</div>
					) : (
						<ul className="mt-4 space-y-3">
							{nearbyBusinesses.map((biz, index) => (
								<li key={`${biz.name ?? "business"}-${index}`} className="rounded-lg border border-[rgba(13,44,114,0.14)] bg-white/65 p-3">
									<p className="font-semibold text-[var(--text-primary)]">{biz.name ?? `Business ${index + 1}`}</p>
									<p className="text-sm text-[var(--text-secondary)]">{biz.address ?? "Address unavailable"}</p>
									{typeof biz.rating === "number" ? (
										<p className="text-xs text-[var(--text-secondary)]">Rating: {biz.rating}</p>
									) : null}
								</li>
							))}
						</ul>
					)}
				</section>
			</div>
		</main>
	);
}
