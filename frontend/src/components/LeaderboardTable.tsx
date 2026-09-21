import { LeaderboardEntry } from "@/lib/types";

function rankClass(rank: number) {
  if (rank === 1) return "rank-1";
  if (rank === 2) return "rank-2";
  if (rank === 3) return "rank-3";
  return "";
}

function medal(rank: number) {
  if (rank === 1) return "🥇";
  if (rank === 2) return "🥈";
  if (rank === 3) return "🥉";
  return null;
}

export default function LeaderboardTable({
  entries,
  highlightUserId,
}: {
  entries: LeaderboardEntry[];
  highlightUserId?: string;
}) {
  if (entries.length === 0) {
    return (
      <div className="py-16 text-center text-muted">
        No scores yet. Be the first to make the board.
      </div>
    );
  }

  return (
    <div className="divide-y divide-border">
      {entries.map((e) => (
        <div
          key={e.user_id}
          className={`flex items-center justify-between px-4 sm:px-6 py-3.5 ${rankClass(
            e.rank
          )} ${e.user_id === highlightUserId ? "ring-1 ring-[#22d3ee]/60" : ""}`}
        >
          <div className="flex items-center gap-4">
            <span className="w-8 text-center font-display font-bold text-lg text-muted">
              {medal(e.rank) || `#${e.rank}`}
            </span>
            <span className="font-medium text-white">{e.username}</span>
            {e.user_id === highlightUserId && (
              <span className="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full bg-[#22d3ee]/15 text-[#22d3ee]">
                you
              </span>
            )}
          </div>
          <span className="font-display font-bold text-lg text-[#39ff88] glow-text">
            {Math.round(e.score).toLocaleString()}
          </span>
        </div>
      ))}
    </div>
  );
}
