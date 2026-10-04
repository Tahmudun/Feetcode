import { useEffect, useRef, useState } from "react";
import { usePlayback } from "./usePlayback";
import Structure from "./Structure";

/**
 * StepPlayer — Feetcode's signature component.
 *
 * Three panes locked to one timeline:
 *   1. Code pane     — the solution, executing line highlighted, footnote
 *                      markers¹ on annotated lines
 *   2. State pane    — every data structure, drawn from the step snapshot
 *   3. Narration bar — one plain-English sentence per step
 *
 * Below the panes: the footnote apparatus. The Footnote Law: everything
 * Feetcode explains is a footnote anchored to a line of code. Hovering a
 * marker highlights its footnote and vice versa; footnotes with a `step`
 * deep-link seek the timeline.
 *
 * Keyboard: ← → step, space play/pause (when the player has focus).
 */
export default function StepPlayer({ script }) {
  const total = script.steps.length;
  const { index, playing, speed, seek, next, prev, toggle, setSpeed } =
    usePlayback(total);
  const step = script.steps[index];
  const footnotes = script.footnotes ?? [];
  const [hotNote, setHotNote] = useState(null); // footnote id under the cursor
  const codeRef = useRef(null);

  // Keep the highlighted line scrolled into view inside the code pane.
  useEffect(() => {
    const el = codeRef.current?.querySelector(".code-line.is-active");
    el?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [index]);

  function onKeyDown(e) {
    if (e.key === "ArrowRight") { e.preventDefault(); next(); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); prev(); }
    else if (e.key === " ") { e.preventDefault(); toggle(); }
  }

  return (
    <section
      className="player"
      tabIndex={0}
      onKeyDown={onKeyDown}
      aria-label="Algorithm step player. Use left and right arrows to step, space to play."
    >
      <header className="player-head">
        <div>
          <h2 className="player-title">{script.title}</h2>
          <span className="player-meta">
            {script.language} · time {script.complexity.time} · space{" "}
            {script.complexity.space}
          </span>
        </div>
        <span className="player-count">
          step {index + 1} <em>/ {total}</em>
        </span>
      </header>

      <div className="player-panes">
        <pre className="code-pane" ref={codeRef}>
          {script.code.map((line, i) => {
            const notes = footnotes.filter((f) => f.line === i);
            return (
              <div
                key={i}
                className={`code-line ${i === step.line ? "is-active" : ""} ${
                  notes.some((n) => n.id === hotNote) ? "is-hot" : ""
                }`}
              >
                <span className="code-num">{i + 1}</span>
                <code>{line || " "}</code>
                {notes.map((n) => (
                  <sup
                    key={n.id}
                    className={`fn-marker ${n.id === hotNote ? "is-hot" : ""}`}
                    onMouseEnter={() => setHotNote(n.id)}
                    onMouseLeave={() => setHotNote(null)}
                  >
                    {n.id}
                  </sup>
                ))}
              </div>
            );
          })}
        </pre>

        <div className="state-pane">
          {step.structures.map((s) => (
            <Structure key={s.id} structure={s} pointers={step.pointers} />
          ))}
          {step.vars.length > 0 && (
            <div className="viz-vars">
              {step.vars.map((v) => (
                <span className={`viz-var st-${v.state}`} key={v.name}>
                  {v.name} = <strong>{v.value}</strong>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      <p className="narration" aria-live="polite" key={index}>
        <sup className="narration-num">{index + 1}</sup> {step.narration}
      </p>

      <div className="transport">
        <button className="t-btn" onClick={prev} disabled={index === 0} aria-label="Previous step">
          ‹
        </button>
        <button className="t-btn t-play" onClick={toggle} aria-label={playing ? "Pause" : "Play"}>
          {playing ? "❚❚" : "▶"}
        </button>
        <button
          className="t-btn"
          onClick={next}
          disabled={index === total - 1}
          aria-label="Next step"
        >
          ›
        </button>

        {/* Scrubber: one tick per step, grouped visually by phase. Clicking a
            tick seeks straight there — possible only because steps are full
            snapshots, never deltas. */}
        <div className="scrubber" role="group" aria-label="Step timeline">
          {script.steps.map((s, i) => (
            <button
              key={i}
              className={`tick ph-${s.phase} ${i === index ? "is-current" : ""} ${
                i < index ? "is-past" : ""
              }`}
              onClick={() => seek(i)}
              aria-label={`Go to step ${i + 1} (${s.phase})`}
            />
          ))}
        </div>

        <div className="speeds">
          {[0.5, 1, 1.5, 2].map((s) => (
            <button
              key={s}
              className={`s-btn ${speed === s ? "is-on" : ""}`}
              onClick={() => setSpeed(s)}
            >
              {s}×
            </button>
          ))}
        </div>
      </div>

      {/* The footnote apparatus. Every analyzer Feetcode grows (the fuzzer,
          the differ, the invariant miner) will emit findings in exactly this
          shape — one output type for the whole system. */}
      {footnotes.length > 0 && (
        <footer className="fn-block">
          <hr className="fn-rule" />
          <ol className="fn-list">
            {footnotes.map((n) => (
              <li
                key={n.id}
                className={`fn-item ${n.id === hotNote ? "is-hot" : ""}`}
                onMouseEnter={() => setHotNote(n.id)}
                onMouseLeave={() => setHotNote(null)}
              >
                <sup className="fn-num">{n.id}</sup>
                <span className="fn-text">
                  {n.text}
                  {Number.isInteger(n.step) && (
                    <button className="fn-jump" onClick={() => seek(n.step)}>
                      → step {n.step + 1}
                    </button>
                  )}
                </span>
              </li>
            ))}
          </ol>
        </footer>
      )}
    </section>
  );
}
