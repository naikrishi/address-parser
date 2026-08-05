import { useQuery } from "@tanstack/react-query";
import { getInputs } from "../api";
import type { InputsListResponse, InputsQueryParams } from "../types";

export const inputsQueryKey = (params: InputsQueryParams = {}): readonly [string, InputsQueryParams] => [
	"inputs",
	params,
];

export function useInputs(params: InputsQueryParams = {}) {
	return useQuery<InputsListResponse>({
		queryKey: inputsQueryKey(params),
		queryFn: () => getInputs(params),
		retry: 1,
		staleTime: 30_000,
	});
}
