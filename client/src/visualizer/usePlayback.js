import { useState, useEffect, useCallback } from "react";

/**
 * usePlayback — owns the Step Player's timeline.
 *
 * Because step scripts are full snapshots, "playback" is nothing more than an
 * index ticking forward on a timer. Seeking backward, scrubbing, or jumping to
 * any step is free: the renderer just draws steps[index]. This hook is the
 * payoff of the snapshot-over-deltas schema decision.
 */
export function usePlayback(totalSteps) {
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1); // multiplier: 0.5, 1, 1.5, 2

  const clamp = useCallback(
    (i) => Math.max(0, Math.min(totalSteps - 1, i)),
    [totalSteps]
  );

  const seek = useCallback((i) => setIndex(clamp(i)), [clamp]);
  const next = useCallback(() => setIndex((i) => clamp(i + 1)), [clamp]);
  const prev = useCallback(() => setIndex((i) => clamp(i - 1)), [clamp]);

  const toggle = useCallback(() => {
    setPlaying((p) => {
      // Pressing play at the end restarts from the top.
      if (!p && index >= totalSteps - 1) setIndex(0);
      return !p;
    });
  }, [index, totalSteps]);

  // The play loop: advance one step every (base / speed) ms while playing.
  useEffect(() => {
    if (!playing) return;
    const interval = setInterval(() => {
      setIndex((i) => {
        if (i >= totalSteps - 1) {
          setPlaying(false); // auto-pause at the final step
          return i;
        }
        return i + 1;
      });
    }, 2400 / speed);
    return () => clearInterval(interval); // cleanup on pause/speed change/unmount
  }, [playing, speed, totalSteps]);

  return { index, playing, speed, seek, next, prev, toggle, setSpeed };
}
