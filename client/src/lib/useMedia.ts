import { useSyncExternalStore } from "react";

/** Subscribe to a CSS media query. Render one layout, not two hidden copies. */
export function useMedia(query: string): boolean {
  return useSyncExternalStore(
    (onChange) => {
      const mql = window.matchMedia(query);
      mql.addEventListener("change", onChange);
      return () => mql.removeEventListener("change", onChange);
    },
    () => window.matchMedia(query).matches,
    () => true,
  );
}

export const useDesktop = () => useMedia("(min-width: 1024px)");
