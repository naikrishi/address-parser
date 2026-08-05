import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks";

export function LoginPage() {
	const { isAuthenticated, login, isLoggingIn } = useAuth();
	const [username, setUsername] = useState("");
	const [password, setPassword] = useState("");
	const [errorMessage, setErrorMessage] = useState<string | null>(null);

	if (isAuthenticated) {
		return <Navigate to="/" replace />;
	}

	async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
		event.preventDefault();
		setErrorMessage(null);

		if (!username.trim() || !password) {
			setErrorMessage("Enter username and password.");
			return;
		}

		try {
			await login({ username: username.trim(), password });
		} catch (error) {
			setErrorMessage(error instanceof Error ? error.message : "Login failed.");
		}
	}

	return (
		<main className="min-h-screen bg-gradient-to-b from-slate-100 via-slate-50 to-white px-4 py-10 sm:px-6 lg:px-8">
			<div className="mx-auto max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
				<p className="text-sm font-semibold uppercase tracking-wide text-slate-500">Address Pipeline</p>
				<h1 className="mt-2 text-2xl font-bold text-slate-900">Sign in</h1>
				<p className="mt-2 text-sm text-slate-600">Use your backend user credentials to access protected routes.</p>

				<form className="mt-6 grid gap-3" onSubmit={(event) => void handleSubmit(event)}>
					<label className="grid gap-1">
						<span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Username</span>
						<input
							type="text"
							value={username}
							onChange={(event) => setUsername(event.target.value)}
							className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-slate-500"
							disabled={isLoggingIn}
						/>
					</label>

					<label className="grid gap-1">
						<span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Password</span>
						<input
							type="password"
							value={password}
							onChange={(event) => setPassword(event.target.value)}
							className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-slate-500"
							disabled={isLoggingIn}
						/>
					</label>

					<button
						type="submit"
						disabled={isLoggingIn}
						className="mt-2 rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-400"
					>
						{isLoggingIn ? "Signing in..." : "Sign in"}
					</button>
				</form>

				{errorMessage ? <p className="mt-3 text-sm text-rose-700">{errorMessage}</p> : null}
			</div>
		</main>
	);
}
