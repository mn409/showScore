import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "showScore — Real-Time Leaderboards",
  description: "A production-ready real-time leaderboard system.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&family=Inter:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-body antialiased">
        <AuthProvider>
          <Navbar />
          <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
