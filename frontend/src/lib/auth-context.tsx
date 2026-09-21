"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
  useCallback,
} from "react";
import { api, getAccessToken, refreshAccessToken, setAccessToken } from "@/lib/api";

export interface UserOut {
  id: string;
  email: string;
  username: string;
  role: "user" | "admin";
  is_active: boolean;
  created_at: string;
}

interface AuthContextValue {
  user: UserOut | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchMe = useCallback(async () => {
    try {
      const res = await api.get<UserOut>("/api/auth/me");
      setUser(res.data);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    (async () => {
      setLoading(true);
      if (!getAccessToken()) {
        const token = await refreshAccessToken();
        if (!token) {
          setLoading(false);
          return;
        }
      }
      await fetchMe();
      setLoading(false);
    })();
  }, [fetchMe]);

  const login = async (email: string, password: string) => {
    const res = await api.post("/api/auth/login", { email, password });
    setAccessToken(res.data.access_token);
    await fetchMe();
  };

  const register = async (email: string, username: string, password: string) => {
    await api.post("/api/auth/register", { email, username, password });
    await login(email, password);
  };

  const logout = async () => {
    await api.post("/api/auth/logout");
    setAccessToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser: fetchMe }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
