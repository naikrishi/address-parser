import { useQuery } from "@tanstack/react-query";
import { ApiError, getParse } from "../api";
import type { ParseResultResponse } from "../types";

export const parseDetailQueryKey = (parseId: string): readonly [string, string] => [
	"parseDetail",
	parseId,
];

export function useParseDetail(parseId: string) {
	return useQuery<ParseResultResponse>({
		queryKey: parseDetailQueryKey(parseId),
		queryFn: () => getParse(parseId),
		enabled: parseId.trim().length > 0,
		retry: (failureCount, error) => {
			if (error instanceof ApiError && (error.status === 401 || error.status === 403 || error.status === 404)) {
				return false;
			}
			return failureCount < 1;
		},
		staleTime: 30_000,
	});
}
