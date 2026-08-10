import { useQuery } from "@tanstack/react-query";
import { ApiError, getInputs } from "../api";
import type { InputsListResponse, InputsQueryParams } from "../types";

export const inputsQueryKey = (params: InputsQueryParams = {}): readonly [string, InputsQueryParams] => [
	"inputs",
	params,
];

export function useInputs(params: InputsQueryParams = {}) {
	return useQuery<InputsListResponse>({
		queryKey: inputsQueryKey(params),
		queryFn: () => getInputs(params),
		retry: (failureCount, error) => {
			if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
				return false;
			}
			return failureCount < 1;
		},
		staleTime: 30_000,
	});
}
