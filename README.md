# showScore

A production-ready, real-time leaderboard system.

**Stack:** FastAPI (async) · PostgreSQL · Redis (sorted sets) · JWT auth · Next.js (App Router) · Celery

This is a fully working reference implementation. Every endpoint below was
built and then verified end-to-end against a live Postgres + Redis instance
before being handed off (see **Verified Test Results** at the bottom).

---

## 1. Architecture

```
Client (Next.js)
      │
      ▼
FastAPI ──► PostgreSQL   (durable score_history, users — source of truth)
   │
   └──────► Redis         (ZADD/ZREVRANK/ZREVRANGE — real-time ranks)

Celery beat/worker ──► reconciles Redis from Postgres, expires old keys,
                        generates analytics snapshots (runs on a schedule)
```

**Data flow:** user submits a score → FastAPI validates (Pydantic + anti-tamper
bounds) → row written to `score_history` in Postgres → the same score is
applied to four Redis sorted sets (`global`, `game:{id}`, `daily:{date}`,
`weekly:{iso-week}`) → the API returns the user's new rank in each scope
immediately → the frontend re-fetches the board.

### Redis keys
| Key | Purpose |
|---|---|
| `leaderboard:global` | all-time, all-games |
| `leaderboard:game:{game_id}` | all-time, one game |
| `leaderboard:daily:{YYYY-MM-DD}` | today only |
| `leaderboard:weekly:{ISO-year}-W{week}` | current ISO week |
| `user:meta:{user_id}` | cached username so boards don't hit Postgres per row |
| `analytics:latest_report` | JSON snapshot written by the nightly Celery job |

### Postgres tables
- `users` — id, email, username, password_hash, role, is_active, created_at
  (`password_hash` is **never** serialized in any API response — see `UserOut` schema)
- `score_history` — id, user_id, game_id, score, score_date, created_at (full audit trail)

### Score update rule
Configurable via `SCORE_UPDATE_RULE` in `.env`:
- `higher_only` (default) — a new score is only stored/ranked if it beats the
  user's previous best for that game (uses Redis `ZADD ... GT`)
- `always_overwrite` — latest submission always wins
- `sum` — scores accumulate (`ZINCRBY`)

### Anti-tampering
- Score bounds (`0` to `1,000,000,000`)
- A single submission cannot exceed 50× the user's previous best for that
  game (flagged as `422` for manual review)
- Rate-limited per IP (`SCORE_SUBMIT_RATE_LIMIT`, default `10/minute`)

---

## 2. Project layout

```
showScore/
  backend/
    app/
      main.py              FastAPI app, CORS, routers, rate-limit handler
      core/                config.py, security.py (JWT/bcrypt), deps.py, limiter.py
      api/routes/           auth.py, scores.py, leaderboard.py, admin.py
      models/               SQLAlchemy: user.py, score.py
      schemas/               Pydantic: user.py, score.py, admin.py
      services/              auth_service, score_service, leaderboard_service, admin_service
      db/                    session.py (async), sync_session.py (for Celery), redis_client.py
      workers/               celery_app.py, tasks.py
    alembic/                 migrations (initial schema included & tested)
    requirements.txt
    Dockerfile
    .env.example
  frontend/
    src/app/                 leaderboard/, login/, register/, profile/, admin/
    src/components/          Navbar, LeaderboardTable
    src/lib/                 api.ts (axios + refresh interceptor), auth-context.tsx, types.ts
    Dockerfile
    .env.local.example
  docker-compose.yml
  .gitignore                 (.env is excluded)
```

---

## 3. Running it

### Option A — Docker Compose (recommended)

```bash
cp backend/.env.example backend/.env
# edit backend/.env and set a real JWT_SECRET_KEY

docker compose up -d postgres redis
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend python -m app.db.bootstrap_admin
docker compose up -d backend celery_worker celery_beat frontend
```

Backend: http://localhost:8000/docs · Frontend: http://localhost:3000

### Option B — Manual

```bash
# 1. Environment
cp backend/.env.example backend/.env
# fill DATABASE_URL, REDIS_URL, JWT_SECRET_KEY

# 2. Services
docker compose up -d postgres redis

# 3. Backend
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python -m app.db.bootstrap_admin  # creates FIRST_ADMIN_EMAIL/PASSWORD from .env
uvicorn app.main:app --reload

# 4. Background workers (separate terminals)
celery -A app.workers.celery_app worker --loglevel=info
celery -A app.workers.celery_app beat --loglevel=info

# 5. Frontend
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

The first admin login is whatever you set `FIRST_ADMIN_EMAIL` /
`FIRST_ADMIN_PASSWORD` to in `.env` (defaults to
`admin@showscore.dev` / `ChangeMe123!` — **change this in production**).

---

## 4. API reference (short form)

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | – | Create account |
| POST | `/api/auth/login` | – | Returns access token + sets HTTPOnly refresh cookie |
| POST | `/api/auth/refresh` | refresh cookie | Rotates access + refresh tokens |
| POST | `/api/auth/logout` | – | Clears refresh cookie |
| GET | `/api/auth/me` | access token | Current user (no password_hash) |
| POST | `/api/scores/submit` | access token | Submit a score (rate-limited) |
| GET | `/api/scores/history` | access token | Caller's score history |
| GET | `/api/leaderboard/global` | – | Top N, all-time |
| GET | `/api/leaderboard/game/{game_id}` | – | Top N for one game |
| GET | `/api/leaderboard/daily` | – | Top N today |
| GET | `/api/leaderboard/weekly` | – | Top N this ISO week |
| GET | `/api/leaderboard/rank/me` | access token | Caller's rank in a scope |
| GET | `/api/leaderboard/rank/{user_id}` | – | Any user's rank in a scope |
| GET | `/api/admin/stats` | admin | Totals |
| GET | `/api/admin/analytics/trend` | admin | Daily submissions/unique users |
| GET | `/api/admin/analytics/top-players` | admin | Top players by scope |
| GET | `/api/admin/health` | admin | DB/Redis health |

Full interactive docs at `/docs` (Swagger) once the backend is running.

---

## 5. Security checklist

- [x] Secrets only in `.env` (never hardcoded); `.env` is git-ignored
- [x] `python-dotenv` / `pydantic-settings` env loading
- [x] Passwords hashed with bcrypt (via passlib)
- [x] Refresh tokens in HTTPOnly, SameSite=Lax cookies (`COOKIE_SECURE=true` in prod)
- [x] Access tokens are short-lived (15 min default) JWTs, `Authorization: Bearer`
- [x] All request bodies validated with Pydantic (types, ranges, regex)
- [x] Score submission rate-limited per IP (slowapi)
- [x] Basic anti-tampering bounds on score deltas
- [x] `password_hash` never present in any response model
- [x] CORS restricted to `CORS_ORIGINS` (comma-separated allowlist)
- [x] Role-based access control (`user` / `admin`) enforced via dependency injection

---

## 6. Verified test results

These were run against a live Postgres 16 + Redis 7 instance with the
actual FastAPI server (not mocked):

| Test | Result |
|---|---|
| Register → success | ✅ `201`, user returned without password_hash |
| Register duplicate email | ✅ `409 Email already registered` |
| Login → token issued | ✅ access token + refresh cookie set |
| Login wrong password | ✅ `401` |
| `/auth/me` without token | ✅ `401` |
| Refresh token flow | ✅ new access token issued from cookie |
| Submit score (new best) | ✅ stored, rank returned for all 4 scopes |
| Submit lower score (`higher_only` rule) | ✅ rejected, reason explained, no DB row created |
| Submit new higher score | ✅ accepted, rank moves to `#1` immediately |
| Global / game / daily leaderboard | ✅ correctly ordered by score desc |
| User rank lookup | ✅ accurate rank + score |
| Score history | ✅ returns caller's own submissions only |
| Admin route as regular user | ✅ `403 Admin privileges required` |
| Admin stats / trend / top-players / health | ✅ all return correct live data |
| Invalid score (`-5`) | ✅ `422` with Pydantic validation detail |
| Frontend `/leaderboard`, `/login`, `/admin` | ✅ all render `200`, production build passes `next build` with zero type errors |

---

## 7. Notes & production hardening ideas

- Swap `SCORE_UPDATE_RULE` per-game if different games need different rules (currently global via env var; trivial to make per-`game_id` in `score_service.py`).
- The weekly/daily Celery reconciliation jobs exist specifically so Redis can be safely flushed/rebuilt from Postgres (source of truth) without losing ranking data.
- For horizontal scaling, put the FastAPI app behind multiple workers (gunicorn + uvicorn workers) — it's fully async and stateless aside from Redis/Postgres.
- Consider Redis Cluster or a managed Redis (e.g. ElastiCache) sorted-set support is standard across all of them.
