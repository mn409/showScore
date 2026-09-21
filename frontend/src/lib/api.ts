import axios from "axios";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: API_URL,
  withCredentials: true, // send HTTPOnly refresh cookie
});

let accessToken: string | null = null;
let refreshPromise: Promise<string | null> | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
  if (typeof window !== "undefined") {
    if (token) sessionStorage.setItem("access_token", token);
    else sessionStorage.removeItem("access_token");
  }
}

export function getAccessToken(): string | null {
  if (accessToken) return accessToken;
  if (typeof window !== "undefined") {
    accessToken = sessionStorage.getItem("access_token");
  }
  return accessToken;
}

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

async function refreshAccessToken(): Promise<string | null> {
  try {
    const res = await axios.post(
      `${API_URL}/api/auth/refresh`,
      {},
      { withCredentials: true }
    );
    const token = res.data.access_token as string;
    setAccessToken(token);
    return token;
  } catch {
    setAccessToken(null);
    return null;
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes("/api/auth/")
    ) {
      originalRequest._retry = true;
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
      }
      const newToken = await refreshPromise;
      if (newToken) {
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      }
    }
    return Promise.reject(error);
  }
);

export { refreshAccessToken };
