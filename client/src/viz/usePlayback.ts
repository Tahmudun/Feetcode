import { useCallback, useEffect, useRef, useState } from "react";

/**
 * The player's clock. Because every step is a complete snapshot, playback is
 * just an index moving on a timer: seeking anywhere is free.
 *
 * A gate can veto forward moves (Predict mode asks a question first). It runs
 * outside React state updaters, which must stay pure.
 */
export function usePlayback(total: number, stepsPerSecond: number, initial = 0) {
  const [index, setIndexState] = useState(() => Math.min(initial, Math.max(0, total - 1)));
  const [playing, setPlaying] = useState(false);
  const indexRef = useRef(index);
  const gate = useRef<((target: number) => boolean) | null>(null);

  const setIndex = useCallback((i: number) => {
    indexRef.current = i;
    setIndexState(i);
  }, []);
  const clamp = useCallback((i: number) => Math.max(0, Math.min(total - 1, i)), [total]);

  const setGate = useCallback((fn: ((target: number) => boolean) | null) => {
    gate.current = fn;
  }, []);

  const seek = useCallback((i: number) => setIndex(clamp(i)), [clamp, setIndex]);

  const advance = useCallback((): boolean => {
    const i = indexRef.current;
    const target = clamp(i + 1);
    if (target === i) return false;
    if (gate.current && !gate.current(target)) return false;
    setIndex(target);
    return true;
  }, [clamp, setIndex]);

  const next = useCallback(() => {
    if (!advance()) setPlaying(false);
  }, [advance]);
  const prev = useCallback(() => setIndex(clamp(indexRef.current - 1)), [clamp, setIndex]);
  const toggle = useCallback(() => {
    setPlaying((p) => {
      if (!p && indexRef.current >= total - 1) setIndex(0);
      return !p;
    });
  }, [total, setIndex]);

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      if (!advance()) setPlaying(false);
    }, 1000 / stepsPerSecond);
    return () => clearInterval(id);
  }, [playing, stepsPerSecond, advance]);

  useEffect(() => {
    if (indexRef.current > total - 1) setIndex(Math.max(0, total - 1));
  }, [total, setIndex]);

  return { index, playing, seek, next, prev, toggle, setPlaying, setGate };
}
