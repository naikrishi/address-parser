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
			setValidationError("Enter an address before you run this.");
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
		<section className="mb-8 panel p-5 reveal-sequence sm:p-6">
			<h2 className="headline text-2xl font-bold">Run Enrichment</h2>
			<p className="subcopy mt-1 text-sm">Paste an address to parse and enrich it.</p>

			<form className="mt-4 grid gap-3" onSubmit={(event) => void handleSubmit(event)}>
				<label className="grid gap-1.5">
					<span className="kicker">Raw Address</span>
					<input
						type="text"
						value={rawAddress}
						onChange={(event) => setRawAddress(event.target.value)}
						placeholder="3400 W Plano Pkwy, Plano, TX 75075, USA"
						className="field px-3 py-2.5 text-sm outline-none ring-0 placeholder:text-slate-400"
						disabled={isSubmitting}
					/>
				</label>

				<div className="grid gap-3 sm:grid-cols-2">
					<label className="grid gap-1.5">
						<span className="kicker">Input Source</span>
						<input
							type="text"
							value={inputSource}
							onChange={(event) => setInputSource(event.target.value)}
							className="field px-3 py-2.5 text-sm outline-none"
							disabled={isSubmitting}
						/>
					</label>

					<label className="grid gap-1.5">
						<span className="kicker">Country Hint</span>
						<input
							type="text"
							value={countryHint}
							onChange={(event) => setCountryHint(event.target.value)}
							placeholder="US"
							className="field px-3 py-2.5 text-sm outline-none"
							disabled={isSubmitting}
						/>
					</label>
				</div>

				<div className="flex items-center gap-3">
					<button
						type="submit"
						disabled={isSubmitting}
						className="cta-primary px-4 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-55"
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
