import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { createParse, runEnrich } from "../api";
import { SearchBox } from "../components";
import { useAuth, useInputs, useParses } from "../hooks";
import type { EnrichResponse, InputListItem, ParseCreateRequest, RankedEnrichResult } from "../types";

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
  const [offset, setOffset] = useState(0);
  const [allItems, setAllItems] = useState<InputListItem[]>([]);

  const { data, isLoading, isError, error, refetch, isFetching } = useInputs({
    limit: LIST_LIMIT,
    offset,
  });
  const { data: parseData } = useParses({
    limit: 200,
    offset: 0,
  });

  // Append on load-more (offset > 0), replace on fresh load (offset === 0).
  useEffect(() => {
    if (!data?.items) return;
    if (offset === 0) {
      setAllItems(data.items);
    } else {
      setAllItems((prev) => {
        const seen = new Set(prev.map((i) => i.id));
        return [...prev, ...data.items.filter((i) => !seen.has(i.id))];
      });
    }
  }, [data, offset]);

  const items = allItems;
  const latestParseByInputId = useMemo(() => {
    const byInputId = new Map<string, string>();
    for (const parse of parseData?.items ?? []) {
      if (!byInputId.has(parse.raw_input_id)) {
        byInputId.set(parse.raw_input_id, parse.id);
      }
    }
    return byInputId;
  }, [parseData]);

  async function handleSearchSubmit(payload: ParseCreateRequest): Promise<void> {
    setIsSubmittingSearch(true);
    setSearchError(null);
    try {
      const parse = await createParse(payload);
      const enrich = await runEnrich({ parse_result_id: parse.id });
      setRankedResults((previous) => rankResults([enrich, ...previous]));
      // Reset to page 1 so the new record appears at the top.
      if (offset === 0) {
        await refetch();
      } else {
        setOffset(0);
      }
    } catch (submitError) {
      setSearchError(submitError instanceof Error ? submitError.message : "Enrichment request failed.");
    } finally {
      setIsSubmittingSearch(false);
    }
  }

  return (
    <main className="page-shell px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <header className="mb-8 reveal-sequence">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="kicker">
              Address Pipeline
            </p>
            <div className="flex items-center gap-3">
              <span className="text-sm text-[var(--text-secondary)]">
                Signed in as {user?.username ?? "unknown"}
              </span>
              <button
                type="button"
                onClick={logout}
                className="cta-secondary px-3 py-1.5 text-xs"
              >
                Logout
              </button>
            </div>
          </div>
          <h1 className="headline mt-2 text-4xl font-bold sm:text-5xl">
            Inputs Feed
          </h1>
          <p className="subcopy mt-3 max-w-3xl text-base">
            Submit an address to run the full flow: libpostal parse, LLM gap fill,
            search fallback, and geocode. Then review past submissions below.
          </p>
        </header>

    {isAdmin ? (
      <SearchBox
        onSubmit={handleSearchSubmit}
        isSubmitting={isSubmittingSearch}
        errorMessage={searchError}
      />
    ) : (
      <section className="mb-8 panel p-5 sm:p-6">
        <h2 className="headline text-2xl font-bold text-amber-900">Read-only role</h2>
        <p className="mt-1 text-sm text-amber-900/85">
          Your current role is <span className="font-semibold">{user?.role ?? "ops"}</span>. Creating parses and running enrichments is restricted to admins.
        </p>
      </section>
    )}

    <section className="mb-8 panel p-5 reveal-sequence sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="headline text-2xl font-bold">Ranked Enrichment Results</h2>
        <span className="neon-pill">CONFIDENCE FIRST</span>
      </div>

      {rankedResults.length === 0 ? (
        <div className="mt-4 rounded-lg border border-dashed border-[rgba(13,44,114,0.2)] py-8 text-center">
          <p className="text-sm font-semibold text-[var(--text-primary)]">No results yet.</p>
          <p className="mt-1 text-xs text-[var(--text-secondary)]">
            {isAdmin ? "Submit an address above to get started." : "Ask an admin to run an enrichment."}
          </p>
        </div>
      ) : (
        <ul className="mt-4 space-y-3">
          {rankedResults.map((result, index) => (
            <li key={`${result.enrichment_result_id}-${result.rank}`} className="rounded-lg border border-[rgba(13,44,114,0.14)] bg-white/65 p-3" style={{ animationDelay: `${index * 70}ms` }}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-[var(--text-primary)]">Rank #{result.rank}</p>
                  <p className="text-xs text-[var(--text-secondary)]">
                    Confidence: {result.confidence_label ?? "unknown"} | Complete: {result.is_complete ? "yes" : "no"}
                  </p>
                </div>
                <Link
                  to={`/parse/${result.parse_result_id}`}
                  className="cta-primary px-3 py-2 text-xs"
                >
                  Open detail
                </Link>
              </div>
            </li>
          ))}
        </ul>
      )}

    </section>

        {isLoading ? (
          <section aria-label="Loading inputs" className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="panel animate-pulse p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="h-5 w-3/5 rounded bg-slate-200" />
                  <div className="h-5 w-16 rounded-full bg-slate-200" />
                </div>
                <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
                  {Array.from({ length: 4 }).map((_, j) => (
                    <div key={j}>
                      <div className="h-3 w-20 rounded bg-slate-200" />
                      <div className="mt-1 h-4 w-8 rounded bg-slate-200" />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </section>
        ) : isError ? (
          <section className="panel border-rose-200 bg-rose-50/85 p-8 text-center text-rose-800">
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
          <section className="panel border-dashed border-[rgba(13,44,114,0.24)] p-10 text-center">
            <p className="text-sm font-semibold text-[var(--text-primary)]">No addresses submitted yet.</p>
            <p className="mt-1 text-xs text-[var(--text-secondary)]">
              {isAdmin ? "Use the enrichment form above to process your first address." : "No records have been submitted yet."}
            </p>
          </section>
        ) : (
          <section className="space-y-3 reveal-sequence">
            <div className="panel flex items-center justify-between rounded-lg px-4 py-3 text-sm text-[var(--text-secondary)]">
              <span>
                Showing {items.length} of {data?.total ?? items.length} records
              </span>
              {isFetching ? <span className="text-[var(--text-secondary)]">Refreshing...</span> : null}
            </div>

            {items.map((item, index) => (
              <article
                key={item.id}
                className="panel p-4"
                style={{ animationDelay: `${index * 55}ms` }}
              >
                <header className="flex flex-wrap items-center justify-between gap-3">
                  <h2 className="min-w-0 break-words headline text-2xl font-bold">{item.raw_address}</h2>
                  <span className="neon-pill">
                    {item.input_source}
                  </span>
                </header>

                <dl className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
                  <div>
                    <dt className="kicker">Country Hint</dt>
                    <dd className="font-semibold text-[var(--text-primary)]">{item.country_hint ?? "N/A"}</dd>
                  </div>
                  <div>
                    <dt className="kicker">Parses</dt>
                    <dd className="font-semibold text-[var(--text-primary)]">{item.parse_result_count}</dd>
                  </div>
                  <div>
                    <dt className="kicker">Enrichments</dt>
                    <dd className="font-semibold text-[var(--text-primary)]">{item.enrichment_result_count}</dd>
                  </div>
                  <div>
                    <dt className="kicker">Geocodes</dt>
                    <dd className="font-semibold text-[var(--text-primary)]">{item.geocode_result_count}</dd>
                  </div>
                </dl>

                <div className="mt-4 flex items-center justify-end">
                  {latestParseByInputId.has(item.id) ? (
                    <Link
                      to={`/parse/${latestParseByInputId.get(item.id)}`}
                      className="cta-primary px-3 py-2 text-xs"
                    >
                      Open latest parse
                    </Link>
                  ) : (
                    <span className="text-xs text-[var(--text-secondary)]">No parse detail available yet</span>
                  )}
                </div>

              </article>
            ))}
            {(data?.total ?? 0) > items.length && (
              <div className="flex justify-center pt-2">
                <button
                  type="button"
                  onClick={() => setOffset((o) => o + LIST_LIMIT)}
                  disabled={isFetching}
                  className="cta-secondary px-5 py-2 text-sm disabled:opacity-50"
                >
                  {isFetching ? "Loading…" : `Load more (${(data?.total ?? 0) - items.length} remaining)`}
                </button>
              </div>
            )}
          </section>
        )}
      </div>
    </main>
  );
}
