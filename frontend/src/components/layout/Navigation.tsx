"use client";

import React from "react";
import {
  Sun,
  Clock,
  Calendar,
  Wind,
  BarChart2,
  Map as MapIcon,
  Info,
  Cpu,
  ShieldAlert,
  Navigation2,
} from "lucide-react";

export type ActiveTab =
  | "dashboard"
  | "live"
  | "hourly"
  | "daily"
  | "airquality"
  | "alerts"
  | "climate"
  | "map"
  | "ml"
  | "sources";

interface NavigationProps {
  activeTab: ActiveTab;
  onSelectTab: (tab: ActiveTab) => void;
}

export function Navigation({ activeTab, onSelectTab }: NavigationProps) {
  const tabs = [
    { id: "dashboard" as const, label: "Overview", icon: Sun },
    { id: "live" as const, label: "Live GPS Monitor", icon: Navigation2 },
    { id: "hourly" as const, label: "72h Hourly", icon: Clock },
    { id: "daily" as const, label: "14d Outlook", icon: Calendar },
    { id: "airquality" as const, label: "Air Quality", icon: Wind },
    { id: "alerts" as const, label: "Early Warning", icon: ShieldAlert },
    { id: "climate" as const, label: "Climate & Heat", icon: BarChart2 },
    { id: "map" as const, label: "Weather Map", icon: MapIcon },
    { id: "ml" as const, label: "Model Studio", icon: Cpu },
    { id: "sources" as const, label: "Transparency", icon: Info },
  ];

  return (
    <nav className="w-full bg-white/70 backdrop-blur-sm border-b border-border-subtle overflow-x-auto custom-scrollbar">
      <div className="max-w-7xl mx-auto flex items-center justify-start sm:justify-center gap-1.5 px-4 py-2 min-w-max">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onSelectTab(tab.id)}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? "bg-brand-sky text-white shadow-sm font-semibold"
                  : "text-ink-secondary hover:text-ink-primary hover:bg-canvas-subtle"
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? "text-white" : "text-ink-muted"}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
