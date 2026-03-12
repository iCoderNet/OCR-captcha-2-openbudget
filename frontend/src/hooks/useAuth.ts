import { create } from "zustand";
import { api } from "../api/client";

interface AuthUser {
  id: string;
  email: string;
  full_name: string | null;
  role: "client" | "admin";
  balance: number;
}

interface AuthState {
  user: AuthUser | null;
  token: string | null;
  setToken: (token: string) => void;
  setUser: (user: AuthUser) => void;
  logout: () => void;
  fetchMe: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem("token"),

  setToken: (token) => {
    localStorage.setItem("token", token);
    set({ token });
  },

  setUser: (user) => set({ user }),

  logout: () => {
    localStorage.removeItem("token");
    set({ user: null, token: null });
    window.location.href = "/login";
  },

  fetchMe: async () => {
    try {
      const { data } = await api.get("/auth/me");
      set({ user: data });
    } catch {
      localStorage.removeItem("token");
      set({ user: null, token: null });
    }
  },
}));
