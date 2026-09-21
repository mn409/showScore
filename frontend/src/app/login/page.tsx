"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      router.push("/leaderboard");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-sm mx-auto mt-12">
      <div className="card p-6 sm:p-8">
        <h1 className="font-display font-bold text-2xl mb-1">
          Welcome <span className="text-[#39ff88]">back</span>
        </h1>
        <p className="text-muted text-sm mb-6">Log in to submit scores and track your rank.</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs uppercase tracking-wide text-muted mb-1">
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-surface2 border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-[#39ff88]"
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-wide text-muted mb-1">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-surface2 border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-[#39ff88]"
            />
          </div>
          {error && <p className="text-sm text-[#ff3d81]">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-md bg-[#39ff88] text-black font-semibold text-sm hover:shadow-neon transition-shadow disabled:opacity-50"
          >
            {loading ? "Logging in…" : "Log in"}
          </button>
        </form>

        <p className="text-sm text-muted mt-5 text-center">
          No account?{" "}
          <Link href="/register" className="text-[#22d3ee] hover:underline">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
