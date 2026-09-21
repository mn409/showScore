"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { ScoreOut, UserRankResponse } from "@/lib/types";

export default function ProfilePage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [globalRank, setGlobalRank] = useState<UserRankResponse | null>(null);
  const [history, setHistory] = useState<ScoreOut[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [authLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    (async () => {
      setLoading(true);
      try {
        const [rankRes, historyRes] = await Promise.all([
          api.get<UserRankResponse>("/api/leaderboard/rank/me", { params: { scope: "global" } }),
          api.get<ScoreOut[]>("/api/scores/history", { params: { limit: 20 } }),
        ]);
        setGlobalRank(rankRes.data);
        setHistory(historyRes.data);
      } finally {
        setLoading(false);
      }
    })();
  }, [user]);

  if (authLoading || !user) {
    return <div className="text-center text-muted py-20">Loading…</div>;
  }

  const bestScore = history.reduce((max, s) => Math.max(max, s.score), 0);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display font-bold text-3xl">
          {user.username}
          <span className="text-muted text-lg font-body font-normal ml-2">
            {user.role === "admin" ? "· admin" : ""}
          </span>
        </h1>
        <p className="text-muted text-sm">{user.email}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card p-5">
          <p className="text-xs uppercase tracking-wide text-muted mb-1">Global Rank</p>
          <p className="font-display font-bold text-3xl text-[#39ff88] glow-text">
            {globalRank?.rank ? `#${globalRank.rank}` : "—"}
          </p>
        </div>
        <div className="card p-5">
          <p className="text-xs uppercase tracking-wide text-muted mb-1">Global Score</p>
          <p className="font-display font-bold text-3xl text-[#22d3ee]">
            {globalRank?.score ? Math.round(globalRank.score).toLocaleString() : "0"}
          </p>
        </div>
        <div className="card p-5">
          <p className="text-xs uppercase tracking-wide text-muted mb-1">Best Single Score</p>
          <p className="font-display font-bold text-3xl text-[#f5d90a]">
            {bestScore.toLocaleString()}
          </p>
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="px-5 py-3 border-b border-border">
          <h2 className="font-display font-semibold text-lg">Recent Scores</h2>
        </div>
        {loading ? (
          <div className="py-12 text-center text-muted">Loading history…</div>
        ) : history.length === 0 ? (
          <div className="py-12 text-center text-muted">No scores submitted yet.</div>
        ) : (
          <div className="divide-y divide-border">
            {history.map((h) => (
              <div key={h.id} className="flex items-center justify-between px-5 py-3">
                <div>
                  <p className="font-medium">{h.game_id}</p>
                  <p className="text-xs text-muted">
                    {new Date(h.created_at).toLocaleString()}
                  </p>
                </div>
                <span className="font-display font-bold text-[#39ff88]">
                  {h.score.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
