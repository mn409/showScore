"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

const links = [
  { href: "/leaderboard", label: "Leaderboard" },
  { href: "/profile", label: "Profile" },
];

export default function Navbar() {
  const { user, logout, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push("/leaderboard");
  };

  return (
    <header className="border-b border-border bg-surface/80 backdrop-blur sticky top-0 z-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <Link href="/leaderboard" className="flex items-center gap-2">
          <span className="font-display font-bold text-2xl tracking-wide text-neon.green glow-text text-[#39ff88]">
            show<span className="text-[#22d3ee]">Score</span>
          </span>
        </Link>

        <nav className="hidden sm:flex items-center gap-6">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`text-sm font-medium transition-colors ${
                pathname === l.href
                  ? "text-[#39ff88]"
                  : "text-muted hover:text-white"
              }`}
            >
              {l.label}
            </Link>
          ))}
          {user?.role === "admin" && (
            <Link
              href="/admin"
              className={`text-sm font-medium transition-colors ${
                pathname === "/admin" ? "text-[#ff3d81]" : "text-muted hover:text-white"
              }`}
            >
              Admin
            </Link>
          )}
        </nav>

        <div className="flex items-center gap-3">
          {loading ? (
            <div className="h-8 w-20 rounded bg-surface2 animate-pulse" />
          ) : user ? (
            <>
              <span className="hidden sm:inline text-sm text-muted">
                Hi, <span className="text-white font-medium">{user.username}</span>
              </span>
              <button
                onClick={handleLogout}
                className="text-sm px-3 py-1.5 rounded-md border border-border hover:border-[#ff3d81] hover:text-[#ff3d81] transition-colors"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="text-sm px-3 py-1.5 rounded-md border border-border hover:border-[#22d3ee] hover:text-[#22d3ee] transition-colors"
              >
                Login
              </Link>
              <Link
                href="/register"
                className="text-sm px-3 py-1.5 rounded-md bg-[#39ff88] text-black font-semibold hover:shadow-neon transition-shadow"
              >
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
