import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { createParse, runEnrich } from "../api";
import { SearchBox } from "../components";
import { useAuth, useInputs } from "../hooks";
import type { EnrichResponse, ParseCreateRequest, RankedEnrichResult } from "../types";

const LIST_LIMIT = 20;

const CONFIDENCE_WEIGHT: Record<string, number> = {
  high: 3,
  medium: 2,
  low: 1,
};

function rankResults(results: EnrichResponse[]): RankedEnrichResult[] {
  const sorted = [...results].sort((a, b) => {
    const aWeight = a.confidence_label ? (CONFIDENCE_WEIGHT[a.confidence_label] ?? 0) : 0;
    const bWeight = b.confidence_label ? (CONFIDENCE_WEIGHT[b.confidence_label] ?? 0) : 0;
    if (aWeight !== bWeight) {
      return bWeight - aWeight;
    }
    if (a.is_complete !== b.is_complete) {
      return a.is_complete ? -1 : 1;
    }
    return Date.parse(b.created_at) - Date.parse(a.created_at);
  });

  return sorted.map((item, index) => ({ ...item, rank: index + 1 }));
}

export function PipelinePage() {
  const { user, logout, isAdmin } = useAuth();
  const [rankedResults, setRankedResults] = useState<RankedEnrichResult[]>([]);
  const [isSubmittingSearch, setIsSubmittingSearch] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const { data, isLoading, isError, error, refetch, isFetching } = useInputs({
    limit: LIST_LIMIT,
    offset: 0,
  });

  const items = data?.items ?? [];

  const topResult = useMemo(() => rankedResults[0], [rankedResults]);

  async function handleSearchSubmit(payload: ParseCreateRequest): Promise<void> {
    setIsSubmittingSearch(true);
    setSearchError(null);
    try {
      const parse = await createParse(payload);
      const enrich = await runEnrich({ parse_result_id: parse.id });
      setRankedResults((previous) => rankResults([enrich, ...previous]));
      await refetch();
    } catch (submitError) {
      setSearchError(submitError instanceof Error ? submitError.message : "Enrichment request failed.");
    } finally {
      setIsSubmittingSearch(false);
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-100 via-slate-50 to-white px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <header className="mb-8">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Address Pipeline
            </p>
            <div className="flex items-center gap-3">
              <span className="text-sm text-slate-600">
                Signed in as {user?.username ?? "unknown"}
              </span>
              <button
                type="button"
                onClick={logout}
                className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100"
              >
                Logout
              </button>
            </div>
          </div>
          <h1 className="mt-2 text-3xl font-bold text-slate-900 sm:text-4xl">
            Inputs Feed
          </h1>
          <p className="mt-3 max-w-3xl text-base text-slate-600">
            Day 12 live integration: this list is loaded from the backend via
            GET /inputs using a typed API client and React Query.
          </p>
        </header>

    {isAdmin ? (
      <SearchBox
        onSubmit={handleSearchSubmit}
        isSubmitting={isSubmittingSearch}
        errorMessage={searchError}
      />
    ) : (
      <section className="mb-8 rounded-xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-amber-900">Read-only role</h2>
        <p className="mt-1 text-sm text-amber-800">
          Your current role is <span className="font-semibold">{user?.role ?? "ops"}</span>. Creating parses and running enrichments is restricted to admins.
        </p>
      </section>
    )}

    <section className="mb-8 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-slate-900">Ranked Enrichment Results</h2>
        <span className="text-sm text-slate-500">Sorted by confidence, then completeness.</span>
      </div>

      {rankedResults.length === 0 ? (
        <p className="mt-3 text-sm text-slate-600">No enrichment runs yet in this session.</p>
      ) : (
        <ul className="mt-4 space-y-3">
          {rankedResults.map((result) => (
            <li key={`${result.enrichment_result_id}-${result.rank}`} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-slate-900">Rank #{result.rank}</p>
                  <p className="text-xs text-slate-600">
                    Confidence: {result.confidence_label ?? "unknown"} | Complete: {result.is_complete ? "yes" : "no"}
                  </p>
                </div>
                <Link
                  to={`/parse/${result.parse_result_id}`}
                  className="rounded-md bg-slate-900 px-3 py-2 text-xs font-semibold text-white hover:bg-slate-700"
                >
                  Open detail
                </Link>
              </div>
            </li>
          ))}
        </ul>
      )}

      {topResult ? (
        <p className="mt-3 text-xs text-slate-500">
          Top result parse id: {topResult.parse_result_id}
        </p>
      ) : null}
    </section>

        {isLoading ? (
          <section className="rounded-xl border border-slate-200 bg-white p-8 text-center text-slate-600 shadow-sm">
            <div className="mx-auto mb-3 h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-700" />
            Loading inputs...
          </section>
        ) : isError ? (
          <section className="rounded-xl border border-rose-200 bg-rose-50 p-8 text-center text-rose-800 shadow-sm">
            <p className="font-semibold">Could not load inputs.</p>
            <p className="mt-2 text-sm">{error instanceof Error ? error.message : "Unknown error"}</p>
            <button
              type="button"
              onClick={() => void refetch()}
              className="mt-4 rounded-md bg-rose-600 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-700"
            >
              Retry
            </button>
          </section>
        ) : items.length === 0 ? (
          <section className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center text-slate-600">
            No parse input records found yet.
          </section>
        ) : (
          <section className="space-y-3">
            <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 shadow-sm">
              <span>
                Showing {items.length} of {data?.total ?? items.length} records
              </span>
              {isFetching ? <span className="text-slate-500">Refreshing...</span> : null}
            </div>

            {items.map((item) => (
              <article
                key={item.id}
                className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
              >
                <header className="flex flex-wrap items-center justify-between gap-3">
                  <h2 className="text-lg font-semibold text-slate-900">{item.raw_address}</h2>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                    {item.input_source}
                  </span>
                </header>

                <dl className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
                  <div>
                    <dt className="text-slate-500">Country Hint</dt>
                    <dd className="font-medium text-slate-800">{item.country_hint ?? "N/A"}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Parses</dt>
                    <dd className="font-medium text-slate-800">{item.parse_result_count}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Enrichments</dt>
                    <dd className="font-medium text-slate-800">{item.enrichment_result_count}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Geocodes</dt>
                    <dd className="font-medium text-slate-800">{item.geocode_result_count}</dd>
                  </div>
                </dl>

              </article>
            ))}
          </section>
        )}
      </div>
    </main>
  );
}
