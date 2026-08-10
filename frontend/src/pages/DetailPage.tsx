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
			<main className="min-h-screen bg-gradient-to-b from-slate-100 via-slate-50 to-white px-4 py-10 sm:px-6 lg:px-8">
				<div className="mx-auto max-w-4xl rounded-xl border border-rose-200 bg-rose-50 p-8 text-rose-800">
					<p className="font-semibold">Missing parse id in route.</p>
					<Link to="/" className="mt-4 inline-block text-sm font-semibold text-slate-900 underline">
						Back to pipeline
					</Link>
				</div>
			</main>
		);
	}

	if (isLoading) {
		return (
			<main className="min-h-screen bg-gradient-to-b from-slate-100 via-slate-50 to-white px-4 py-10 sm:px-6 lg:px-8">
				<div className="mx-auto max-w-4xl rounded-xl border border-slate-200 bg-white p-8 text-center text-slate-600 shadow-sm">
					<div className="mx-auto mb-3 h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-700" />
					Loading parse detail...
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
			<main className="min-h-screen bg-gradient-to-b from-slate-100 via-slate-50 to-white px-4 py-10 sm:px-6 lg:px-8">
				<div className="mx-auto max-w-4xl rounded-xl border border-rose-200 bg-rose-50 p-8 text-center text-rose-800 shadow-sm">
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
		<main className="min-h-screen bg-gradient-to-b from-slate-100 via-slate-50 to-white px-4 py-10 sm:px-6 lg:px-8">
			<div className="mx-auto max-w-5xl">
				<header className="mb-8">
					<p className="text-sm font-semibold uppercase tracking-wide text-slate-500">Address Pipeline</p>
					<h1 className="mt-2 text-3xl font-bold text-slate-900 sm:text-4xl">Detail View</h1>
					<p className="mt-3 text-base text-slate-600">
						Raw input, parse output, enrichment, search step, geocode, and nearby businesses.
					</p>
					<div className="mt-4 flex items-center gap-4 text-sm">
						<Link to="/" className="font-semibold text-slate-800 underline">
							Back to pipeline
						</Link>
						{isFetching ? <span className="text-slate-500">Refreshing...</span> : null}
					</div>
				</header>

				<section className="mb-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
					<h2 className="text-lg font-semibold text-slate-900">Raw Input</h2>
					<p className="mt-2 text-slate-800">{data.raw_input.raw_address}</p>
					<dl className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
						<div>
							<dt className="text-slate-500">Input Source</dt>
							<dd className="font-medium text-slate-800">{data.raw_input.input_source}</dd>
						</div>
						<div>
							<dt className="text-slate-500">Country Hint</dt>
							<dd className="font-medium text-slate-800">{data.raw_input.country_hint ?? "N/A"}</dd>
						</div>
						<div>
							<dt className="text-slate-500">Parser</dt>
							<dd className="font-medium text-slate-800">{data.parser_name}</dd>
						</div>
						<div>
							<dt className="text-slate-500">Parse Confidence</dt>
							<dd className="font-medium text-slate-800">{data.confidence_score}</dd>
						</div>
					</dl>
				</section>

				<section className="mb-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
					<h2 className="text-lg font-semibold text-slate-900">Parsed Components</h2>
					<dl className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
						{Object.entries(data.parsed_components).map(([key, value]) => (
							<div key={key} className="rounded-md bg-slate-50 px-3 py-2">
								<dt className="text-xs font-medium uppercase text-slate-500">{key}</dt>
								<dd className="text-sm font-medium text-slate-800">{value ?? "N/A"}</dd>
							</div>
						))}
					</dl>
				</section>

				<section className="mb-6 grid gap-4">
					{steps.map((step) => (
						<StepCard key={step.id} step={step} />
					))}
				</section>

				<section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
					<h2 className="text-lg font-semibold text-slate-900">Nearby Businesses</h2>
					{nearbyBusinesses.length === 0 ? (
						<p className="mt-2 text-sm text-slate-600">No nearby businesses were returned.</p>
					) : (
						<ul className="mt-4 space-y-3">
							{nearbyBusinesses.map((biz, index) => (
								<li key={`${biz.name ?? "business"}-${index}`} className="rounded-md border border-slate-200 bg-slate-50 p-3">
									<p className="font-semibold text-slate-900">{biz.name ?? `Business ${index + 1}`}</p>
									<p className="text-sm text-slate-700">{biz.address ?? "Address unavailable"}</p>
									{typeof biz.rating === "number" ? (
										<p className="text-xs text-slate-500">Rating: {biz.rating}</p>
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
