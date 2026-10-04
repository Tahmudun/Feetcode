import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Theme = "dark" | "light";

interface Settings {
  theme: Theme;
  fontSize: number;
  vim: boolean;
  speed: number; // playback steps per second
  heatmap: boolean; // show line-hit heat in the editor after profiling
  setTheme: (t: Theme) => void;
  toggleTheme: () => void;
  set: (patch: Partial<Omit<Settings, "set" | "setTheme" | "toggleTheme">>) => void;
}

function applyTheme(t: Theme) {
  document.documentElement.dataset.theme = t;
  try {
    localStorage.setItem("fc:theme", t);
  } catch {
    /* ignore */
  }
}

export const useSettings = create<Settings>()(
  persist(
    (set, get) => ({
      theme: (document.documentElement.dataset.theme as Theme) || "dark",
      fontSize: 14,
      vim: false,
      speed: 2,
      heatmap: true,
      setTheme: (theme) => {
        applyTheme(theme);
        set({ theme });
      },
      toggleTheme: () => get().setTheme(get().theme === "dark" ? "light" : "dark"),
      set: (patch) => set(patch),
    }),
    {
      name: "fc:settings",
      onRehydrateStorage: () => (state) => {
        if (state) applyTheme(state.theme);
      },
    },
  ),
);
