"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
} from "recharts";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import LeaderboardTable from "@/components/LeaderboardTable";
import { LeaderboardEntry } from "@/lib/types";

interface SystemStats {
  total_users: number;
  total_scores_submitted: number;
  total_games: number;
  scores_submitted_today: number;
}

interface DailyActivity {
  day: string;
  submissions: number;
  unique_users: number;
}

interface HealthMetrics {
  database: string;
  redis: string;
  environment: string;
}

function StatCard({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="card p-5">
      <p className="text-xs uppercase tracking-wide text-muted mb-1">{label}</p>
      <p className={`font-display font-bold text-3xl`} style={{ color }}>
        {value}
      </p>
    </div>
  );
}

export default function AdminPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [trend, setTrend] = useState<DailyActivity[]>([]);
  const [topDaily, setTopDaily] = useState<LeaderboardEntry[]>([]);
  const [health, setHealth] = useState<HealthMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [forbidden, setForbidden] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [authLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    if (user.role !== "admin") {
      setForbidden(true);
      setLoading(false);
      return;
    }
    (async () => {
      setLoading(true);
      try {
        const [statsRes, trendRes, topRes, healthRes] = await Promise.all([
          api.get<SystemStats>("/api/admin/stats"),
          api.get<{ trend: DailyActivity[] }>("/api/admin/analytics/trend", {
            params: { days: 14 },
          }),
          api.get<{ players: any[] }>("/api/admin/analytics/top-players", {
            params: { scope: "daily", top: 10 },
          }),
          api.get<HealthMetrics>("/api/admin/health"),
        ]);
        setStats(statsRes.data);
        setTrend(trendRes.data.trend);
        setTopDaily(
          topRes.data.players.map((p) => ({
            rank: p.rank,
            user_id: p.user_id,
            username: p.username,
            score: p.score,
          }))
        );
        setHealth(healthRes.data);
      } finally {
        setLoading(false);
      }
    })();
  }, [user]);

  if (authLoading || loading) {
    return <div className="text-center text-muted py-20">Loading admin dashboard…</div>;
  }

  if (forbidden) {
    return (
      <div className="text-center py-20">
        <p className="text-[#ff3d81] font-display text-2xl mb-2">Access denied</p>
        <p className="text-muted">Admin privileges are required to view this page.</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display font-bold text-3xl">
          Admin <span className="text-[#ff3d81]">Dashboard</span>
        </h1>
        <p className="text-muted mt-1">System analytics and health at a glance.</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="Total Users" value={stats?.total_users ?? 0} color="#39ff88" />
        <StatCard label="Total Scores" value={stats?.total_scores_submitted ?? 0} color="#22d3ee" />
        <StatCard label="Games Tracked" value={stats?.total_games ?? 0} color="#f5d90a" />
        <StatCard label="Submitted Today" value={stats?.scores_submitted_today ?? 0} color="#ff3d81" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-5">
          <h2 className="font-display font-semibold text-lg mb-4">
            Submissions — Last 14 Days
          </h2>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={trend}>
              <CartesianGrid stroke="#232b3a" strokeDasharray="3 3" />
              <XAxis dataKey="day" stroke="#7d8797" fontSize={11} tickFormatter={(d) => d.slice(5)} />
              <YAxis stroke="#7d8797" fontSize={11} allowDecimals={false} />
              <Tooltip
                contentStyle={{ background: "#171d29", border: "1px solid #232b3a", borderRadius: 8 }}
                labelStyle={{ color: "#e7ecf3" }}
              />
              <Line
                type="monotone"
                dataKey="submissions"
                stroke="#39ff88"
                strokeWidth={2}
                dot={false}
                name="Submissions"
              />
              <Line
                type="monotone"
                dataKey="unique_users"
                stroke="#22d3ee"
                strokeWidth={2}
                dot={false}
                name="Unique Users"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-5">
          <h2 className="font-display font-semibold text-lg mb-4">Top Players Today</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={topDaily.slice(0, 8)}>
              <CartesianGrid stroke="#232b3a" strokeDasharray="3 3" />
              <XAxis dataKey="username" stroke="#7d8797" fontSize={11} />
              <YAxis stroke="#7d8797" fontSize={11} />
              <Tooltip
                contentStyle={{ background: "#171d29", border: "1px solid #232b3a", borderRadius: 8 }}
                labelStyle={{ color: "#e7ecf3" }}
              />
              <Bar dataKey="score" fill="#f5d90a" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card overflow-hidden">
          <div className="px-5 py-3 border-b border-border">
            <h2 className="font-display font-semibold text-lg">Today's Leaderboard</h2>
          </div>
          <LeaderboardTable entries={topDaily} />
        </div>

        <div className="card p-5">
          <h2 className="font-display font-semibold text-lg mb-4">System Health</h2>
          <div className="space-y-3">
            <HealthRow label="Database" status={health?.database} />
            <HealthRow label="Redis" status={health?.redis} />
            <div className="flex items-center justify-between text-sm pt-2 border-t border-border">
              <span className="text-muted">Environment</span>
              <span className="font-medium uppercase text-xs px-2 py-1 rounded bg-surface2">
                {health?.environment}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function HealthRow({ label, status }: { label: string; status?: string }) {
  const ok = status === "ok";
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-muted">{label}</span>
      <span
        className={`flex items-center gap-1.5 font-medium ${
          ok ? "text-[#39ff88]" : "text-[#ff3d81]"
        }`}
      >
        <span
          className={`h-2 w-2 rounded-full ${ok ? "bg-[#39ff88]" : "bg-[#ff3d81]"}`}
        />
        {status ?? "unknown"}
      </span>
    </div>
  );
}
