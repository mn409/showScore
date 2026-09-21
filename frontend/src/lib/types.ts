export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  username: string;
  score: number;
}

export interface LeaderboardResponse {
  scope: string;
  entries: LeaderboardEntry[];
  total_entries: number;
}

export interface UserRankResponse {
  scope: string;
  user_id: string;
  username: string;
  score: number | null;
  rank: number | null;
}

export interface ScoreOut {
  id: string;
  user_id: string;
  game_id: string;
  score: number;
  score_date: string;
  created_at: string;
}

export interface ScoreSubmitResponse {
  accepted: boolean;
  reason: string;
  score: ScoreOut | null;
  global_rank: number | null;
  game_rank: number | null;
  daily_rank: number | null;
  weekly_rank: number | null;
}
