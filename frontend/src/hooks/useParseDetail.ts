import { useQuery } from "@tanstack/react-query";
import { getParse } from "../api";
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
		retry: 1,
		staleTime: 30_000,
	});
}
