import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { clearAuthTokens, getAccessToken, getMe, login, onAuthExpired } from "../api";
import type { LoginRequest } from "../types";

const meQueryKey = ["auth", "me"] as const;

export function useAuth() {
	const queryClient = useQueryClient();

	const meQuery = useQuery({
		queryKey: meQueryKey,
		queryFn: () => getMe(),
		retry: false,
		staleTime: 30_000,
		enabled: Boolean(getAccessToken()),
	});

	const loginMutation = useMutation({
		mutationFn: (payload: LoginRequest) => login(payload),
		onSuccess: async () => {
			await queryClient.invalidateQueries({ queryKey: meQueryKey });
			await queryClient.refetchQueries({ queryKey: meQueryKey, type: "active" });
		},
	});

	useEffect(() => {
		const unsubscribe = onAuthExpired(() => {
			clearAuthTokens();
			queryClient.cancelQueries();
			queryClient.clear();
		});
		return unsubscribe;
	}, [queryClient]);

	function logout(): void {
		clearAuthTokens();
		queryClient.cancelQueries();
		queryClient.clear();
	}

	return {
		user: meQuery.data?.user ?? null,
		isAuthenticated: Boolean(meQuery.data?.user),
		isAdmin: meQuery.data?.user?.role === "admin",
		isLoading: meQuery.isLoading,
		error: meQuery.error,
		login: loginMutation.mutateAsync,
		isLoggingIn: loginMutation.isPending,
		logout,
	};
}
