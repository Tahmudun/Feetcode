import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { usePlayback } from "./usePlayback";

const STEPS = 5; // indices 0..4

describe("usePlayback", () => {
  it("starts at step 0, paused, at 1x speed", () => {
    const { result } = renderHook(() => usePlayback(STEPS));
    expect(result.current.index).toBe(0);
    expect(result.current.playing).toBe(false);
    expect(result.current.speed).toBe(1);
  });

  it("next/prev step through the timeline and clamp at both ends", () => {
    const { result } = renderHook(() => usePlayback(STEPS));

    act(() => result.current.prev());
    expect(result.current.index).toBe(0); // clamped at start

    act(() => result.current.next());
    expect(result.current.index).toBe(1);

    for (let i = 0; i < 10; i++) act(() => result.current.next());
    expect(result.current.index).toBe(STEPS - 1); // clamped at end
  });

  it("seek jumps anywhere and clamps out-of-range targets", () => {
    const { result } = renderHook(() => usePlayback(STEPS));

    act(() => result.current.seek(3));
    expect(result.current.index).toBe(3);

    act(() => result.current.seek(99));
    expect(result.current.index).toBe(STEPS - 1);

    act(() => result.current.seek(-4));
    expect(result.current.index).toBe(0);
  });

  it("toggle flips playing on and off", () => {
    const { result } = renderHook(() => usePlayback(STEPS));

    act(() => result.current.toggle());
    expect(result.current.playing).toBe(true);

    act(() => result.current.toggle());
    expect(result.current.playing).toBe(false);
  });

  it("pressing play at the final step restarts from the top", () => {
    const { result } = renderHook(() => usePlayback(STEPS));

    act(() => result.current.seek(STEPS - 1));
    act(() => result.current.toggle());
    expect(result.current.playing).toBe(true);
    expect(result.current.index).toBe(0);
  });

  describe("the play loop (fake timers)", () => {
    beforeEach(() => vi.useFakeTimers());
    afterEach(() => vi.useRealTimers());

    it("advances one step every 2400ms at 1x", () => {
      const { result } = renderHook(() => usePlayback(STEPS));

      act(() => result.current.toggle());
      act(() => vi.advanceTimersByTime(2400));
      expect(result.current.index).toBe(1);

      act(() => vi.advanceTimersByTime(2400 * 2));
      expect(result.current.index).toBe(3);
    });

    it("scales the tick to 2400/speed ms", () => {
      const { result } = renderHook(() => usePlayback(STEPS));

      act(() => result.current.setSpeed(2));
      act(() => result.current.toggle());

      act(() => vi.advanceTimersByTime(1200));
      expect(result.current.index).toBe(1);

      act(() => vi.advanceTimersByTime(1199));
      expect(result.current.index).toBe(1); // not yet

      act(() => vi.advanceTimersByTime(1));
      expect(result.current.index).toBe(2);
    });

    it("auto-pauses on the final step and stays there", () => {
      const { result } = renderHook(() => usePlayback(STEPS));

      act(() => result.current.toggle());
      act(() => vi.advanceTimersByTime(2400 * 10));

      expect(result.current.index).toBe(STEPS - 1);
      expect(result.current.playing).toBe(false);

      act(() => vi.advanceTimersByTime(2400 * 3));
      expect(result.current.index).toBe(STEPS - 1); // no zombie interval
    });

    it("does not tick while paused", () => {
      const { result } = renderHook(() => usePlayback(STEPS));

      act(() => vi.advanceTimersByTime(2400 * 3));
      expect(result.current.index).toBe(0);
    });
  });
});
