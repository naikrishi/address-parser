export type PipelineStepStatus =
	| "complete"
	| "in_progress"
	| "error"
	| "pending"
	| "skipped";

export interface PipelineStep {
	id: number;
	title: string;
	status: PipelineStepStatus;
	summary: string;
	details?: Record<string, string | number | null>;
}

export interface InputListItem {
	id: string;
	raw_address: string;
	input_source: string;
	country_hint: string | null;
	created_at: string;
	parse_result_count: number;
	enrichment_result_count: number;
	geocode_result_count: number;
	has_enrichment: boolean;
	has_geocode: boolean;
}

export interface InputsListResponse {
	items: InputListItem[];
	total: number;
	limit: number;
	offset: number;
}

export interface ParseListItem {
	id: string;
	raw_input_id: string;
	parser_name: string;
	is_complete: boolean;
	confidence_score: number;
	created_at: string;
	raw_address: string;
	input_source: string;
	country_hint: string | null;
	enrichment_result_count: number;
	geocode_result_count: number;
	latest_enrichment_status: string | null;
	latest_geocode_status: string | null;
}

export interface ParseListResponse {
	items: ParseListItem[];
	total: number;
	limit: number;
	offset: number;
}

export interface InputsQueryParams {
	limit?: number;
	offset?: number;
	input_source?: string;
	country_hint?: string;
	has_parse_results?: boolean;
	has_enrichment?: boolean;
	has_geocode?: boolean;
}

export interface ParseCreateRequest {
	raw_address: string;
	input_source?: string;
	country_hint?: string | null;
}

export interface LoginRequest {
	username: string;
	password: string;
}

export interface TokenResponse {
	access_token: string;
	refresh_token: string;
	token_type: string;
}

export interface AuthUser {
	id: string;
	email: string;
	username: string;
	role: "ops" | "admin";
	is_active: boolean;
	created_at: string;
}

export interface AuthMeResponse {
	user: AuthUser;
}

export interface RawInputSummary {
	id: string;
	raw_address: string;
	input_source: string;
	country_hint: string | null;
	created_at: string;
}

export interface EnrichmentResultResponse {
	id: string;
	parse_result_id: string;
	provider_name: string;
	status: string;
	enriched_components: Record<string, string | null>;
	is_complete: boolean;
	confidence_score: number | null;
	error_message: string | null;
	created_at: string;
}

export interface GeocodePayloadBusiness {
	name?: string;
	address?: string;
	category?: string;
	rating?: number;
	phone?: string;
	website?: string;
}

export interface GeocodeResultResponse {
	id: string;
	parse_result_id: string;
	enrichment_result_id: string | null;
	provider_name: string;
	status: string;
	latitude: number | null;
	longitude: number | null;
	result_payload: Record<string, unknown>;
	error_message: string | null;
	created_at: string;
}

export interface ParseResultResponse {
	id: string;
	raw_input_id: string;
	parser_name: string;
	parsed_components: Record<string, string | null>;
	is_complete: boolean;
	confidence_score: number;
	created_at: string;
	raw_input: RawInputSummary;
	enrichment_results: EnrichmentResultResponse[];
	geocode_results: GeocodeResultResponse[];
}

export interface EnrichmentStepTrace {
	step: number;
	provider: string;
	status: "complete" | "partial" | "skipped" | "error";
	prompt_tokens: number;
	completion_tokens: number;
	estimated_cost: number;
}

export interface EnrichRequest {
	parse_result_id: string;
}

export interface EnrichResponse {
	parse_result_id: string;
	enrichment_result_id: string;
	geocode_result_id: string | null;
	enriched_components: Record<string, string | null>;
	is_complete: boolean;
	confidence_label: "low" | "medium" | "high" | null;
	latitude: number | null;
	longitude: number | null;
	steps: EnrichmentStepTrace[];
	total_estimated_cost: number;
	created_at: string;
}

export interface RankedEnrichResult extends EnrichResponse {
	rank: number;
}
