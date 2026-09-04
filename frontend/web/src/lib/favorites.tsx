"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useAuth } from "./auth";
import { apiClient } from "./api";

interface FavoritesContextType {
  favoriteIds: Set<string>;
  isFavorite: (propertyId: string) => boolean;
  toggleFavorite: (propertyId: string) => Promise<boolean>;
  isLoading: boolean;
}

const FavoritesContext = createContext<FavoritesContextType>({
  favoriteIds: new Set(),
  isFavorite: () => false,
  toggleFavorite: async () => false,
  isLoading: false,
});

export function FavoritesProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [favoriteIds, setFavoriteIds] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);

  const fetchFavoriteIds = useCallback(async () => {
    if (!user) {
      setFavoriteIds(new Set());
      return;
    }

    try {
      setIsLoading(true);
      const favList = await apiClient.listFavorites({ limit: 100 });
      setFavoriteIds(new Set(favList.map((p) => p.id)));
    } catch {
      // Ignore errors when unauthenticated or offline
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchFavoriteIds();
  }, [fetchFavoriteIds]);

  const isFavorite = useCallback(
    (propertyId: string) => favoriteIds.has(propertyId),
    [favoriteIds]
  );

  const toggleFavorite = useCallback(
    async (propertyId: string): Promise<boolean> => {
      if (!user) {
        window.location.href = "/login?redirect=" + encodeURIComponent(window.location.pathname + window.location.search);
        return false;
      }

      // Optimistic update
      const wasFav = favoriteIds.has(propertyId);
      setFavoriteIds((prev) => {
        const next = new Set(prev);
        if (wasFav) {
          next.delete(propertyId);
        } else {
          next.add(propertyId);
        }
        return next;
      });

      try {
        const res = await apiClient.toggleFavorite(propertyId);
        // Ensure state aligns with backend truth
        setFavoriteIds((prev) => {
          const next = new Set(prev);
          if (res.is_favorite) {
            next.add(propertyId);
          } else {
            next.delete(propertyId);
          }
          return next;
        });
        return res.is_favorite;
      } catch (err) {
        // Rollback on failure
        setFavoriteIds((prev) => {
          const next = new Set(prev);
          if (wasFav) {
            next.add(propertyId);
          } else {
            next.delete(propertyId);
          }
          return next;
        });
        throw err;
      }
    },
    [user, favoriteIds]
  );

  return (
    <FavoritesContext.Provider value={{ favoriteIds, isFavorite, toggleFavorite, isLoading }}>
      {children}
    </FavoritesContext.Provider>
  );
}

export function useFavorites() {
  return useContext(FavoritesContext);
}
