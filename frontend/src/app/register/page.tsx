"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register(email, username, password);
      router.push("/leaderboard");
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-sm mx-auto mt-12">
      <div className="card p-6 sm:p-8">
        <h1 className="font-display font-bold text-2xl mb-1">
          Join <span className="text-[#39ff88]">showScore</span>
        </h1>
        <p className="text-muted text-sm mb-6">Create an account to climb the ranks.</p>

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
              Username
            </label>
            <input
              required
              minLength={3}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              pattern="^[a-zA-Z0-9_]+$"
              title="Letters, numbers, and underscores only"
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
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-surface2 border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-[#39ff88]"
            />
            <p className="text-[11px] text-muted mt-1">
              8+ characters, at least one letter and one number.
            </p>
          </div>
          {error && <p className="text-sm text-[#ff3d81]">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-md bg-[#39ff88] text-black font-semibold text-sm hover:shadow-neon transition-shadow disabled:opacity-50"
          >
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="text-sm text-muted mt-5 text-center">
          Already have an account?{" "}
          <Link href="/login" className="text-[#22d3ee] hover:underline">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
