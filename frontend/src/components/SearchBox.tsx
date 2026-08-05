import { FormEvent, useState } from "react";
import type { ParseCreateRequest } from "../types";

interface SearchBoxProps {
	onSubmit: (payload: ParseCreateRequest) => Promise<void>;
	isSubmitting: boolean;
	errorMessage?: string | null;
}

export function SearchBox({ onSubmit, isSubmitting, errorMessage }: SearchBoxProps) {
	const [rawAddress, setRawAddress] = useState("");
	const [inputSource, setInputSource] = useState("manual");
	const [countryHint, setCountryHint] = useState("");
	const [validationError, setValidationError] = useState<string | null>(null);

	async function handleSubmit(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		const trimmed = rawAddress.trim();
		if (!trimmed) {
			setValidationError("Enter a raw address before running enrichment.");
			return;
		}
		setValidationError(null);

		await onSubmit({
			raw_address: trimmed,
			input_source: inputSource.trim() || "manual",
			country_hint: countryHint.trim() || null,
		});
	}

	return (
		<section className="mb-8 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
			<h2 className="text-lg font-semibold text-slate-900">Run Enrichment</h2>
			<p className="mt-1 text-sm text-slate-600">
				Paste a raw address, create a parse result, and run the Day 10 enrichment pipeline.
			</p>

			<form className="mt-4 grid gap-3" onSubmit={(event) => void handleSubmit(event)}>
				<label className="grid gap-1">
					<span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Raw address</span>
					<input
						type="text"
						value={rawAddress}
						onChange={(event) => setRawAddress(event.target.value)}
						placeholder="3400 W Plano Pkwy, Plano, TX 75075, USA"
						className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none ring-0 placeholder:text-slate-400 focus:border-slate-500"
						disabled={isSubmitting}
					/>
				</label>

				<div className="grid gap-3 sm:grid-cols-2">
					<label className="grid gap-1">
						<span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Input source</span>
						<input
							type="text"
							value={inputSource}
							onChange={(event) => setInputSource(event.target.value)}
							className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-slate-500"
							disabled={isSubmitting}
						/>
					</label>

					<label className="grid gap-1">
						<span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Country hint</span>
						<input
							type="text"
							value={countryHint}
							onChange={(event) => setCountryHint(event.target.value)}
							placeholder="US"
							className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-slate-500"
							disabled={isSubmitting}
						/>
					</label>
				</div>

				<div className="flex items-center gap-3">
					<button
						type="submit"
						disabled={isSubmitting}
						className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-400"
					>
						{isSubmitting ? "Running..." : "Run enrich"}
					</button>
				</div>
			</form>

			{validationError ? <p className="mt-3 text-sm text-rose-700">{validationError}</p> : null}
			{errorMessage ? <p className="mt-3 text-sm text-rose-700">{errorMessage}</p> : null}
		</section>
	);
}
