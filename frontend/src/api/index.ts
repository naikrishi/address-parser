import type {
	AuthMeResponse,
	EnrichRequest,
	EnrichResponse,
	InputsListResponse,
	InputsQueryParams,
	LoginRequest,
	ParseListResponse,
	ParseCreateRequest,
	ParseResultResponse,
	TokenResponse,
} from "../types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() || "http://127.0.0.1:8000";

const TOKEN_STORAGE_KEY = "address_parser_access_token";
const REFRESH_TOKEN_STORAGE_KEY = "address_parser_refresh_token";
const AUTH_EXPIRED_EVENT_NAME = "address-parser:auth-expired";

export class ApiError extends Error {
	status: number;

	constructor(status: number, message: string) {
		super(message);
		this.status = status;
	}
}

export function setAccessToken(token: string): void {
	if (typeof window === "undefined") {
		return;
	}
	window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function getAccessToken(): string | null {
	if (typeof window === "undefined") {
		return null;
	}
	return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function clearAccessToken(): void {
	if (typeof window === "undefined") {
		return;
	}
	window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export function setRefreshToken(token: string): void {
	if (typeof window === "undefined") {
		return;
	}
	window.localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, token);
}

export function getRefreshToken(): string | null {
	if (typeof window === "undefined") {
		return null;
	}
	return window.localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY);
}

export function clearRefreshToken(): void {
	if (typeof window === "undefined") {
		return;
	}
	window.localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY);
}

export function clearAuthTokens(): void {
	clearAccessToken();
	clearRefreshToken();
}

export function emitAuthExpired(): void {
	if (typeof window === "undefined") {
		return;
	}
	window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT_NAME));
}

export function onAuthExpired(callback: () => void): () => void {
	if (typeof window === "undefined") {
		return () => {};
	}
	const handler = () => callback();
	window.addEventListener(AUTH_EXPIRED_EVENT_NAME, handler);
	return () => {
		window.removeEventListener(AUTH_EXPIRED_EVENT_NAME, handler);
	};
}

function buildQueryString(params: InputsQueryParams = {}): string {
	const query = new URLSearchParams();

	for (const [key, value] of Object.entries(params)) {
		if (value === undefined || value === null || value === "") {
			continue;
		}
		query.set(key, String(value));
	}

	const serialized = query.toString();
	return serialized ? `?${serialized}` : "";
}

function normalizeApiError(error: unknown): string {
	if (error instanceof ApiError) {
		return error.message;
	}
	if (error instanceof Error && error.message) {
		return error.message;
	}
	return "Unexpected error while loading inputs.";
}

async function readErrorMessage(response: Response): Promise<string> {
	const body = await response.text();
	return `Request failed (${response.status}): ${body || response.statusText}`;
}

async function requestJson<T>(url: string, init: RequestInit): Promise<T> {
	try {
		const response = await fetch(url, init);
		const hasAuthorizationHeader =
			init.headers instanceof Headers
				? init.headers.has("Authorization")
				: Boolean((init.headers as Record<string, string> | undefined)?.Authorization);

		if (!response.ok) {
			const apiError = new ApiError(response.status, await readErrorMessage(response));
			if (apiError.status === 401 && hasAuthorizationHeader) {
				emitAuthExpired();
			}
			throw apiError;
		}

		return (await response.json()) as T;
	} catch (error) {
		if (error instanceof ApiError) {
			throw error;
		}
		throw new Error(normalizeApiError(error));
	}
}

function withAuthHeaders(headers: Record<string, string> = {}): Record<string, string> {
	const token = getAccessToken();
	if (!token) {
		return headers;
	}
	return {
		...headers,
		Authorization: `Bearer ${token}`,
	};
}

export async function login(payload: LoginRequest): Promise<TokenResponse> {
	const url = `${API_BASE_URL}/auth/token`;
	const response = await requestJson<TokenResponse>(url, {
		method: "POST",
		headers: {
			Accept: "application/json",
			"Content-Type": "application/json",
		},
		body: JSON.stringify(payload),
	});

	setAccessToken(response.access_token);
	setRefreshToken(response.refresh_token);
	return response;
}

export async function getMe(): Promise<AuthMeResponse> {
	const url = `${API_BASE_URL}/auth/me`;

	return requestJson<AuthMeResponse>(url, {
		method: "GET",
		headers: withAuthHeaders({
			Accept: "application/json",
		}),
	});
}

export async function getInputs(params: InputsQueryParams = {}): Promise<InputsListResponse> {
	const url = `${API_BASE_URL}/inputs${buildQueryString(params)}`;

	return requestJson<InputsListResponse>(url, {
		method: "GET",
		headers: withAuthHeaders({
			Accept: "application/json",
		}),
	});
}

export async function createParse(payload: ParseCreateRequest): Promise<ParseResultResponse> {
	const url = `${API_BASE_URL}/parse`;

	return requestJson<ParseResultResponse>(url, {
		method: "POST",
		headers: withAuthHeaders({
			Accept: "application/json",
			"Content-Type": "application/json",
		}),
		body: JSON.stringify(payload),
	});
}

export async function getParse(parseId: string): Promise<ParseResultResponse> {
	const url = `${API_BASE_URL}/parse/${parseId}`;

	return requestJson<ParseResultResponse>(url, {
		method: "GET",
		headers: withAuthHeaders({
			Accept: "application/json",
		}),
	});
}

export async function getParses(params: InputsQueryParams = {}): Promise<ParseListResponse> {
	const url = `${API_BASE_URL}/parses${buildQueryString(params)}`;

	return requestJson<ParseListResponse>(url, {
		method: "GET",
		headers: withAuthHeaders({
			Accept: "application/json",
		}),
	});
}

export async function runEnrich(payload: EnrichRequest): Promise<EnrichResponse> {
	const url = `${API_BASE_URL}/enrich`;

	return requestJson<EnrichResponse>(url, {
		method: "POST",
		headers: withAuthHeaders({
			Accept: "application/json",
			"Content-Type": "application/json",
		}),
		body: JSON.stringify(payload),
	});
}
