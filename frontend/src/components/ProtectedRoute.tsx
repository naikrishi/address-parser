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
			<main className="min-h-screen bg-gradient-to-b from-slate-100 via-slate-50 to-white px-4 py-10 sm:px-6 lg:px-8">
				<div className="mx-auto max-w-xl rounded-xl border border-slate-200 bg-white p-8 text-center text-slate-600 shadow-sm">
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
