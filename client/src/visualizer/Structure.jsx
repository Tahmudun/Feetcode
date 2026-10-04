/**
 * Structure renderers. Each is a pure function of one step's snapshot — no
 * internal state, no memory of previous steps. Cross-step animation happens
 * "for free": elements keep stable React keys, so when a cell's state changes
 * between snapshots, CSS transitions on background/border/transform tween it.
 *
 * To support a new structure type (stack, linked list...), add a renderer here
 * and a case in <Structure/>. The schema's unknown types are ignored, so old
 * clients never crash on new scripts.
 */

function ArrayStructure({ structure, pointers }) {
  const ptrs = pointers.filter((p) => p.structure === structure.id);
  return (
    <div className="viz-structure">
      <span className="viz-label">{structure.label}</span>
      <div className="viz-array">
        {structure.cells.map((cell, i) => {
          const ptr = ptrs.find((p) => p.index === i);
          return (
            <div className="viz-slot" key={i}>
              <div className={`viz-cell st-${cell.state}`}>{cell.v}</div>
              <div className="viz-under">
                <span className="viz-index">{i}</span>
                {ptr && <span className="viz-pointer">▲ {ptr.label}</span>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MapStructure({ structure }) {
  return (
    <div className="viz-structure">
      <span className="viz-label">{structure.label}</span>
      <div className="viz-map">
        {structure.entries.length === 0 && (
          <div className="viz-map-empty">{ "{ }" } empty</div>
        )}
        {structure.entries.map((e) => (
          // Keyed by the map key itself: an entry keeps its DOM node across
          // steps, so state changes animate instead of remounting.
          <div className={`viz-entry st-${e.state}`} key={e.k}>
            <span className="viz-key">{e.k}</span>
            <span className="viz-arrow">→</span>
            <span className="viz-val">{e.v}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Structure({ structure, pointers }) {
  switch (structure.type) {
    case "array":
      return <ArrayStructure structure={structure} pointers={pointers} />;
    case "map":
      return <MapStructure structure={structure} />;
    default:
      return null; // forward compatibility: skip types this client doesn't know
  }
}
