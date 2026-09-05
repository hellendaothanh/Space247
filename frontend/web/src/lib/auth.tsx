"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { UserResponse } from "@shared/types";
import { apiClient } from "./api";

interface AuthContextType {
  user: UserResponse | null;
  token: string | null;
  isLoading: boolean;
  login: (token: string, user: UserResponse) => void;
  logout: () => void;
  updateUser: (user: UserResponse) => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  isLoading: true,
  login: () => {},
  logout: () => {},
  updateUser: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const savedToken = localStorage.getItem("space247_token");
    const savedUser = localStorage.getItem("space247_user");

    if (savedToken) {
      setToken(savedToken);
      if (savedUser) {
        try {
          setUser(JSON.parse(savedUser));
        } catch {
          // ignore corrupted json
        }
      }

      // Verify token with backend
      apiClient
        .getCurrentUser()
        .then((userData) => {
          setUser(userData);
          localStorage.setItem("space247_user", JSON.stringify(userData));
        })
        .catch((err: any) => {
          // Only wipe credentials if explicitly 401 Unauthorized or 403 Forbidden
          const errMsg = String(err?.message || "");
          if (errMsg.includes("401") || errMsg.includes("403")) {
            logout();
          }
        })
        .finally(() => {
          setIsLoading(false);
        });
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = (newToken: string, newUser: UserResponse) => {
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem("space247_token", newToken);
    localStorage.setItem("space247_user", JSON.stringify(newUser));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("space247_token");
    localStorage.removeItem("space247_user");
  };

  const updateUser = (newUser: UserResponse) => {
    setUser(newUser);
    localStorage.setItem("space247_user", JSON.stringify(newUser));
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
