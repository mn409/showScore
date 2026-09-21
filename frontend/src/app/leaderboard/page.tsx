"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { LeaderboardResponse, ScoreSubmitResponse } from "@/lib/types";
import LeaderboardTable from "@/components/LeaderboardTable";

type Scope = "global" | "game" | "daily" | "weekly";

const SCOPES: { key: Scope; label: string }[] = [
  { key: "global", label: "Global" },
  { key: "daily", label: "Today" },
  { key: "weekly", label: "This Week" },
  { key: "game", label: "By Game" },
];

export default function LeaderboardPage() {
  const { user } = useAuth();
  const [scope, setScope] = useState<Scope>("global");
  const [gameId, setGameId] = useState("chess");
  const [board, setBoard] = useState<LeaderboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [submitGame, setSubmitGame] = useState("chess");
  const [submitScore, setSubmitScore] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState<ScoreSubmitResponse | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const fetchBoard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const path =
        scope === "game" ? `/api/leaderboard/game/${encodeURIComponent(gameId)}` : `/api/leaderboard/${scope}`;
      const res = await api.get<LeaderboardResponse>(path, { params: { top: 25 } });
      setBoard(res.data);
    } catch (e) {
      setError("Could not load leaderboard. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }, [scope, gameId]);

  useEffect(() => {
    fetchBoard();
  }, [fetchBoard]);

  const handleSubmitScore = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    setSubmitResult(null);
    const scoreNum = Number(submitScore);
    if (!submitGame.trim() || Number.isNaN(scoreNum) || scoreNum < 0) {
      setSubmitError("Enter a valid game id and a non-negative score.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post<ScoreSubmitResponse>("/api/scores/submit", {
        game_id: submitGame.trim(),
        score: scoreNum,
      });
      setSubmitResult(res.data);
      setSubmitScore("");
      fetchBoard();
    } catch (err: any) {
      setSubmitError(err?.response?.data?.detail || "Failed to submit score.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display font-bold text-3xl sm:text-4xl tracking-tight">
          <span className="text-[#39ff88] glow-text">Live</span> Leaderboard
        </h1>
        <p className="text-muted mt-1">Real-time ranks powered by Redis sorted sets.</p>
      </div>

      {user && (
        <form
          onSubmit={handleSubmitScore}
          className="card p-4 sm:p-5 flex flex-col sm:flex-row gap-3 sm:items-end"
        >
          <div className="flex-1">
            <label className="block text-xs uppercase tracking-wide text-muted mb-1">
              Game ID
            </label>
            <input
              value={submitGame}
              onChange={(e) => setSubmitGame(e.target.value)}
              className="w-full bg-surface2 border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-[#39ff88]"
              placeholder="chess"
            />
          </div>
          <div className="flex-1">
            <label className="block text-xs uppercase tracking-wide text-muted mb-1">
              Score
            </label>
            <input
              value={submitScore}
              onChange={(e) => setSubmitScore(e.target.value)}
              type="number"
              min={0}
              className="w-full bg-surface2 border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-[#39ff88]"
              placeholder="1000"
            />
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="px-5 py-2 rounded-md bg-[#39ff88] text-black font-semibold text-sm hover:shadow-neon transition-shadow disabled:opacity-50"
          >
            {submitting ? "Submitting…" : "Submit score"}
          </button>
        </form>
      )}

      {submitError && <p className="text-sm text-[#ff3d81]">{submitError}</p>}
      {submitResult && (
        <div
          className={`text-sm rounded-md px-4 py-2 border ${
            submitResult.accepted
              ? "border-[#39ff88]/40 text-[#39ff88] bg-[#39ff88]/5"
              : "border-[#f5d90a]/40 text-[#f5d90a] bg-[#f5d90a]/5"
          }`}
        >
          {submitResult.accepted ? "Score stored." : submitResult.reason}
          {submitResult.global_rank && ` — global rank #${submitResult.global_rank}`}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2">
        {SCOPES.map((s) => (
          <button
            key={s.key}
            onClick={() => setScope(s.key)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-colors ${
              scope === s.key
                ? "bg-[#22d3ee]/15 border-[#22d3ee] text-[#22d3ee]"
                : "border-border text-muted hover:text-white"
            }`}
          >
            {s.label}
          </button>
        ))}
        {scope === "game" && (
          <input
            value={gameId}
            onChange={(e) => setGameId(e.target.value)}
            className="bg-surface2 border border-border rounded-full px-4 py-1.5 text-sm focus:outline-none focus:border-[#22d3ee]"
            placeholder="game id…"
          />
        )}
      </div>

      <div className="card overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-muted">Loading ranks…</div>
        ) : error ? (
          <div className="py-16 text-center text-[#ff3d81]">{error}</div>
        ) : (
          <LeaderboardTable entries={board?.entries || []} highlightUserId={user?.id} />
        )}
      </div>
    </div>
  );
}
