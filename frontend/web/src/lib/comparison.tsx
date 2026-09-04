"use client";

import { createContext, useContext, useState, ReactNode } from "react";
import { PropertyResponse, SearchResultItem } from "@shared/types";

export interface ComparisonContextType {
  selectedProperties: PropertyResponse[];
  toggleComparison: (property: PropertyResponse) => void;
  clearComparison: () => void;
  isSelected: (id: string) => boolean;
}

const ComparisonContext = createContext<ComparisonContextType | undefined>(undefined);

export function ComparisonProvider({ children }: { children: ReactNode }) {
  const [selectedProperties, setSelectedProperties] = useState<PropertyResponse[]>([]);

  const toggleComparison = (property: PropertyResponse) => {
    setSelectedProperties((prev) => {
      const isSelected = prev.some((p) => p.id === property.id);
      if (isSelected) {
        return prev.filter((p) => p.id !== property.id);
      }
      if (prev.length >= 3) {
        // You could trigger a toast here if you have a toast system
        alert("Chỉ có thể so sánh tối đa 3 bất động sản.");
        return prev;
      }
      return [...prev, property];
    });
  };

  const clearComparison = () => setSelectedProperties([]);

  const isSelected = (id: string) => selectedProperties.some((p) => p.id === id);

  return (
    <ComparisonContext.Provider
      value={{ selectedProperties, toggleComparison, clearComparison, isSelected }}
    >
      {children}
    </ComparisonContext.Provider>
  );
}

export function useComparison() {
  const context = useContext(ComparisonContext);
  if (!context) {
    throw new Error("useComparison must be used within a ComparisonProvider");
  }
  return context;
}
