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
		<main className="page-shell px-4 sm:px-6 lg:px-8">
			<div className="mx-auto max-w-md panel p-7 reveal-sequence sm:p-8">
				<div>
					<p className="kicker">Address Pipeline</p>
					<h1 className="headline mt-2 text-3xl font-bold">Control Room Login</h1>
					<p className="subcopy mt-2 text-sm">Sign in with your account to access the app.</p>
				</div>

				<form className="mt-2 grid gap-3" onSubmit={(event) => void handleSubmit(event)}>
					<label className="grid gap-1.5">
						<span className="kicker">Username</span>
						<input
							type="text"
							value={username}
							onChange={(event) => setUsername(event.target.value)}
							className="field px-3 py-2.5 text-sm outline-none"
							disabled={isLoggingIn}
						/>
					</label>

					<label className="grid gap-1.5">
						<span className="kicker">Password</span>
						<input
							type="password"
							value={password}
							onChange={(event) => setPassword(event.target.value)}
							className="field px-3 py-2.5 text-sm outline-none"
							disabled={isLoggingIn}
						/>
					</label>

					<button
						type="submit"
						disabled={isLoggingIn}
						className="cta-primary mt-2 px-4 py-2.5 text-sm disabled:cursor-not-allowed disabled:opacity-55"
					>
						{isLoggingIn ? "Signing in..." : "Sign in"}
					</button>
				</form>

				{errorMessage ? <p className="mt-1 text-sm text-rose-700">{errorMessage}</p> : null}
			</div>
		</main>
	);
}
