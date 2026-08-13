import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks";

interface ProtectedRouteProps {
	children: JSX.Element;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
	const location = useLocation();
	const { isAuthenticated, isLoading } = useAuth();

	if (isLoading) {
		return (
			<main className="page-shell px-4 sm:px-6 lg:px-8">
				<div className="mx-auto max-w-xl panel p-8 text-center text-[var(--text-secondary)]">
					<div className="mx-auto mb-3 h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-700" />
					Checking session...
				</div>
			</main>
		);
	}

	if (!isAuthenticated) {
		return <Navigate to="/login" replace state={{ from: location }} />;
	}

	return children;
}
