import { useQuery } from "@tanstack/react-query";
import { ApiError, getParses } from "../api";
import type { InputsQueryParams, ParseListResponse } from "../types";

export const parsesQueryKey = (params: InputsQueryParams = {}): readonly [string, InputsQueryParams] => [
	"parses",
	params,
];

export function useParses(params: InputsQueryParams = {}) {
	return useQuery<ParseListResponse>({
		queryKey: parsesQueryKey(params),
		queryFn: () => getParses(params),
		retry: (failureCount, error) => {
			if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
				return false;
			}
			return failureCount < 1;
		},
		staleTime: 30_000,
	});
}