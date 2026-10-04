import { Link } from "react-router-dom";
import { PROBLEMS, PATTERNS } from "../data/problems";

export default function Home() {
  return (
    <main className="page">
      <header className="hero">
        <p className="wordmark">
          feetcode<sup className="wordmark-sup">1</sup>
        </p>
        <h1 className="hero-line">
          Watch algorithms <em>run</em>.
        </h1>
        <p className="hero-sub">
          Free, pattern-first DSA prep. Every solution plays step by step —
          code, data structures, and plain English on one scrubbable timeline —
          and everything worth knowing is a footnote pinned to the exact line
          it's about. No paywall, ever.
        </p>
        <Link className="cta" to="/problems/group-anagrams">
          ▶ Play Group Anagrams
        </Link>
        <p className="hero-fn">
          <sup className="fn-num">1</sup> yes, the name is a pun. the footnotes
          are real.
        </p>
      </header>

      {PATTERNS.map((pattern) => {
        const items = PROBLEMS.filter((p) => p.pattern === pattern);
        if (items.length === 0) return null;
        return (
          <section className="pattern-block" key={pattern}>
            <h2 className="pattern-name">{pattern}</h2>
            <ul className="problem-list">
              {items.map((p) =>
                p.live ? (
                  <li key={p.id}>
                    <Link className="problem-row is-live" to={`/problems/${p.id}`}>
                      <span className="row-title">{p.title}</span>
                      <span className={`diff diff-${p.difficulty.toLowerCase()}`}>
                        {p.difficulty}
                      </span>
                      <span className="row-go">visualize →</span>
                    </Link>
                  </li>
                ) : (
                  <li key={p.id}>
                    <div className="problem-row">
                      <span className="row-title">{p.title}</span>
                      <span className={`diff diff-${p.difficulty.toLowerCase()}`}>
                        {p.difficulty}
                      </span>
                      <span className="row-soon">in the lab</span>
                    </div>
                  </li>
                )
              )}
            </ul>
          </section>
        );
      })}

      <footer className="foot-note">
        built by Tahmudun · open source · MIT
      </footer>
    </main>
  );
}
