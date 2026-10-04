import { useParams, Link } from "react-router-dom";
import { PROBLEMS } from "../data/problems";
import StepPlayer from "../visualizer/StepPlayer";
import groupAnagrams from "../data/steps/group-anagrams.json";

// Registry of step scripts. When the AI pipeline lands (Phase 1.5), this
// becomes a dynamic import keyed by filename — for now, explicit is clearer.
const SCRIPTS = {
  "group-anagrams": [groupAnagrams],
};

export default function ProblemPage() {
  const { id } = useParams();
  const problem = PROBLEMS.find((p) => p.id === id);
  const scripts = SCRIPTS[id] ?? [];

  if (!problem) {
    return (
      <main className="page">
        <p className="missing">
          No problem with that id. <Link to="/">Back to the list</Link>.
        </p>
      </main>
    );
  }

  return (
    <main className="page">
      <nav className="crumbs">
        <Link to="/">feetcode</Link>
        <span>/</span>
        <span>{problem.pattern}</span>
      </nav>

      <header className="problem-head">
        <h1>{problem.title}</h1>
        <span className={`diff diff-${problem.difficulty.toLowerCase()}`}>
          {problem.difficulty}
        </span>
      </header>

      <p className="statement">{problem.statement}</p>
      {problem.example && <pre className="example">{problem.example}</pre>}

      {problem.insight && (
        <aside className="insight">
          <span className="insight-tag">the pattern</span>
          <p>{problem.insight}</p>
        </aside>
      )}

      {scripts.length > 0 ? (
        scripts.map((s) => <StepPlayer key={s.solutionId} script={s} />)
      ) : (
        <p className="missing">Visualization for this one is still in the lab.</p>
      )}

      {problem.references?.length > 0 && (
        <footer className="refs">
          <hr className="fn-rule" />
          <span className="refs-tag">references</span>
          <ol className="fn-list">
            {problem.references.map((r, i) => {
              // Numbering continues after the solution's footnotes, like a
              // single scholarly apparatus running down the page.
              const offset = scripts.reduce(
                (sum, s) => sum + (s.footnotes?.length ?? 0),
                0
              );
              return (
                <li className="fn-item" key={i}>
                  <sup className="fn-num">{offset + i + 1}</sup>
                  <span className="fn-text">{r}</span>
                </li>
              );
            })}
          </ol>
        </footer>
      )}
    </main>
  );
}
