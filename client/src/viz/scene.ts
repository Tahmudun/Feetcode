/**
 * buildScene(trace, i, ctx) -> everything needed to draw step i.
 *
 * A pure function of one snapshot (plus the previous one, for "what changed"),
 * so the player can jump to any step instantly and every renderer is dumb.
 *
 * It answers, for arbitrary user code:
 *   - how should each variable be drawn?   (array / bars / chars / grid / map / set / stack / linked graph)
 *   - which scalars are pointers into which array?
 *   - what did this line do?               (from the engine's recorded accesses: compare, read, write, push, pop, probe)
 *   - what changed since the last step?    (snapshot diff)
 * A per-problem lens can override any of these choices; without one, heuristics take over.
 */
import type { Lens } from "@/content/types";
import type { Access, Frame, Heap, HeapObj, PyVal, Step, Trace } from "@/runtime/types";
import { deref, field, isNodeObj, isRef, letterCounts, num, pyRepr, scalarText } from "./decode";
import { evalExpr } from "./expr";
import { computeOverlay, type Overlay } from "./overlays";
import { layoutGraph, type GraphLayout } from "./graph";

export type CellState = "idle" | "active" | "compare" | "match" | "miss" | "new" | "changed" | "removed" | "oob";

export interface CellView {
  text: string;
  value: number | null;
  state: CellState;
  ref?: number;
}

export interface PointerView {
  name: string;
  index: number;
  tone: number;
}

interface PanelBase {
  key: string;
  names: string[];
  heapId?: number;
}

export interface ArrayPanel extends PanelBase {
  kind: "array";
  view: "cells" | "bars" | "chars";
  container: string;
  cells: CellView[];
  pointers: PointerView[];
  window?: [number, number];
  marked?: { by: string; indices: number[] };
  ghost?: { index: number; text: string };
  probe?: { text: string; hit: boolean };
  oob?: number;
  truncated?: number;
  overlay?: Overlay;
}

export interface StackPanel extends PanelBase {
  kind: "stack";
  container: string;
  items: CellView[];
  ghost?: CellView;
  probe?: { text: string; hit: boolean };
  indexInto?: string;
}

export interface MapEntryView {
  key: string;
  value: string;
  state: CellState;
  valueRef?: number;
}

export interface MapPanel extends PanelBase {
  kind: "map";
  subtype?: string;
  entries: MapEntryView[];
  probe?: { text: string; hit: boolean };
  ghost?: { key: string; value: string };
  truncated?: number;
}

export interface SetPanel extends PanelBase {
  kind: "set";
  items: CellView[];
  probe?: { text: string; hit: boolean };
}

export interface GridPanel extends PanelBase {
  kind: "grid";
  rows: CellView[][];
  box?: number;
}

export interface GraphNodeView {
  id: number;
  label: string;
  cls: string;
  row: number;
  col: number;
  state: CellState;
  vars: string[];
}

export interface GraphEdgeView {
  from: number;
  to: number;
  kind: "next" | "prev" | "random";
  state: "idle" | "new";
}

export interface GraphPanel extends PanelBase {
  kind: "graph";
  nodes: GraphNodeView[];
  edges: GraphEdgeView[];
  nulls: string[];
  rows: number;
  cols: number;
}

export interface ObjectPanel extends PanelBase {
  kind: "object";
  cls: string;
  fields: { name: string; value: string }[];
}

export type Panel = ArrayPanel | StackPanel | MapPanel | SetPanel | GridPanel | GraphPanel | ObjectPanel;

export interface VarView {
  name: string;
  text: string;
  state: "idle" | "changed" | "new";
  pointer: boolean;
}

export interface FrameView {
  fn: string;
  id: number;
  line: number;
  args: string;
}

export interface Scene {
  index: number;
  step: Step;
  line: number;
  next?: number;
  branch?: 0 | 1;
  narration: string;
  authored: boolean;
  panels: Panel[];
  vars: VarView[];
  frames: FrameView[];
  ret?: string;
  exc?: string;
  stdout: string;
}

export interface SceneContext {
  lens: Lens;
  params: string[];
  graph: GraphLayout;
  codeLines: string[];
}

export function makeContext(trace: Trace, lens: Lens = {}, params: string[] = []): SceneContext {
  return { lens, params, graph: layoutGraph(trace), codeLines: trace.code.split("\n") };
}

const POINTER_NAME = /^(i|j|l|r|left|right|lo|hi|low|high|mid|start|end|slow|fast|p|q|ptr|idx|index|cur|curr|pos|buy|sell|top|anchor|read|write|first|last|begin|ii|jj)$/;
const NODE_POINTER_NAME = /^(prev|curr|cur|nxt|next|head|tail|slow|fast|dummy|node|first|second|l1|l2|list1|list2|left|right|kth|group_prev|group_next|p|q|a|b|temp|tmp|new_head|newHead|copy|lru|t1|t2|slow2|odd|even|h)$/;
const STACK_NAME = /(^|_)(stack|stk|st|path|mins|minstack|min_stack|monostack)$/i;

const TONES = 5;
function toneFor(name: string): number {
  const fixed: Record<string, number> = { l: 0, left: 0, i: 0, slow: 0, lo: 0, r: 1, right: 1, j: 1, fast: 1, hi: 1, mid: 2, k: 2 };
  if (name in fixed) return fixed[name];
  let h = 0;
  for (const ch of name) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return h % TONES;
}

/** Top-frame variables, with `self` expanded into `self.field` entries. */
function visibleVars(frame: Frame | undefined, heap: Heap, lens: Lens): [string, PyVal][] {
  if (!frame) return [];
  const hide = new Set(lens.hide ?? []);
  const out: [string, PyVal][] = [];
  for (const [name, v] of frame.v) {
    if (hide.has(name)) continue;
    if (name === "self") {
      const obj = deref(heap, v);
      if (obj && obj[0] === "obj" && !isNodeObj(obj)) {
        for (const [f, fv] of obj[2]) if (!hide.has(`self.${f}`)) out.push([`self.${f}`, fv]);
        continue;
      }
    }
    out.push([name, v]);
  }
  return out;
}

function cellOf(v: PyVal, heap: Heap, quote = false): CellView {
  if (isRef(v)) return { text: pyRepr(v, heap, 2), value: null, state: "idle", ref: v.r };
  return { text: scalarText(v, quote), value: num(v), state: "idle" };
}

function isGrid(obj: HeapObj, heap: Heap): boolean {
  if (obj[0] !== "list" || obj[1].length < 2) return false;
  let width = -1;
  for (const row of obj[1]) {
    const r = deref(heap, row);
    if (!r || r[0] !== "list" || r[1].some((x) => isRef(x))) return false;
    if (width >= 0 && r[1].length !== width) return false;
    width = r[1].length;
  }
  return width > 1;
}

function frameArgs(frame: Frame, heap: Heap): string {
  return frame.v
    .filter(([n]) => n !== "self")
    .slice(0, 4)
    .map(([n, v]) => `${n}=${pyRepr(v, heap, 1)}`)
    .join(", ");
}

export function buildScene(trace: Trace, index: number, ctx: SceneContext): Scene {
  const step = trace.steps[index];
  const prev = index > 0 ? trace.steps[index - 1] : undefined;
  const heap = step.h;
  const top = step.s[step.s.length - 1];
  const lens = ctx.lens;
  const roots = visibleVars(top, heap, lens);

  const panels: Panel[] = [];
  const byHeap = new Map<number, Panel>();
  const byName = new Map<string, Panel>();
  const vars: VarView[] = [];
  const intVars: Record<string, number> = {};
  let hasNodes = false;

  for (const [name, v] of roots) {
    if (typeof v === "number" && Number.isInteger(v)) intVars[name] = v;
    if (!isRef(v)) {
      const asArray = typeof v === "string" && v.length > 0 && v.length <= 80 && (lens.arrays?.[name] || ctx.params.includes(name));
      if (asArray) {
        const s = v as string;
        const panel: ArrayPanel = {
          kind: "array", key: `str:${name}`, names: [name], view: "chars", container: "str",
          cells: [...s].map((ch) => ({ text: ch, value: null, state: "idle" })), pointers: [],
        };
        panels.push(panel);
        byName.set(name, panel);
        continue;
      }
      vars.push({ name, text: scalarText(v), state: "idle", pointer: v === null && NODE_POINTER_NAME.test(name.replace(/^self\./, "")) });
      continue;
    }
    const obj = heap[String(v.r)];
    if (!obj) continue;
    if (isNodeObj(obj)) {
      hasNodes = true;
      continue;
    }
    const existing = byHeap.get(v.r);
    if (existing) {
      existing.names.push(name);
      byName.set(name, existing);
      continue;
    }
    const panel = makePanel(name, v.r, obj, heap, lens);
    if (!panel) continue;
    if (panelHasNodes(obj, heap)) hasNodes = true;
    panels.push(panel);
    byHeap.set(v.r, panel);
    byName.set(name, panel);
  }

  // Linked structures: one graph panel for every node object reachable from the frame.
  if (hasNodes || roots.some(([, v]) => isRef(v) && isNodeObj(heap[String(v.r)]))) {
    const graph = buildGraphPanel(step, roots, ctx);
    if (graph.nodes.length) panels.unshift(graph);
  }

  attachPointers(panels, roots, intVars, ctx);
  applyIndexes(byName, heap, lens);
  applyAccesses(panels, byHeap, byName, step, prev);
  diffPanels(panels, step, prev);
  diffVars(vars, top, prev);

  for (const p of panels) {
    if (p.kind === "array" && (lens.overlay || p.view === "bars")) {
      const ov = computeOverlay(lens.overlay, p, intVars, roots, heap);
      if (ov) p.overlay = ov;
    }
  }

  const frames = step.s.map((f) => ({ fn: f.f, id: f.id, line: f.l, args: frameArgs(f, heap) }));
  const stdout = trace.stdout ? trace.stdout.slice(0, step.o ?? trace.stdout.length) : "";
  return {
    index,
    step,
    line: step.l,
    next: step.n,
    branch: step.b,
    narration: step.t ?? "",
    authored: Boolean(step.t),
    panels,
    vars,
    frames,
    ret: step.k === "return" && step.r !== undefined ? pyRepr(step.r, heap, 3) : undefined,
    exc: step.k === "exc" ? step.x : undefined,
    stdout,
  };
}

function panelHasNodes(obj: HeapObj, heap: Heap): boolean {
  const items: PyVal[] = obj[0] === "dict" ? obj[1].flatMap(([k, v]) => [k, v]) : obj[0] === "obj" ? obj[2].map(([, v]) => v) : obj[1];
  return items.some((x) => {
    const o = deref(heap, x);
    if (!o) return false;
    if (isNodeObj(o)) return true;
    return o[0] === "tuple" && o[1].some((y) => isNodeObj(deref(heap, y)));
  });
}

function makePanel(name: string, id: number, obj: HeapObj, heap: Heap, lens: Lens): Panel | null {
  const bare = name.replace(/^self\./, "");
  const kind = obj[0];
  if (kind === "dict") {
    const keyFmt = lens.maps?.[name]?.key;
    return {
      kind: "map", key: `h${id}`, names: [name], heapId: id, subtype: obj[3] ?? undefined,
      truncated: obj[2] ?? undefined,
      entries: obj[1].map(([k, v]) => ({
        key: (keyFmt === "letter-counts" && letterCounts(k, heap)) || pyRepr(k, heap, 2),
        value: pyRepr(v, heap, 2),
        state: "idle" as CellState,
        valueRef: isRef(v) ? v.r : undefined,
      })),
    };
  }
  if (kind === "set") {
    return { kind: "set", key: `h${id}`, names: [name], heapId: id, items: obj[1].map((x) => cellOf(x, heap, true)) };
  }
  if (kind === "obj") {
    return {
      kind: "object", key: `h${id}`, names: [name], heapId: id, cls: obj[1],
      fields: obj[2].map(([f, v]) => ({ name: f, value: pyRepr(v, heap, 2) })),
    };
  }
  // list / tuple / deque
  if (lens.grids?.includes(name) || (lens.grids === undefined && isGrid(obj, heap))) {
    const rows = obj[1].map((r) => {
      const row = deref(heap, r);
      return row && row[0] !== "obj" && row[0] !== "dict" ? row[1].map((x) => cellOf(x as PyVal, heap)) : [];
    });
    return { kind: "grid", key: `h${id}`, names: [name], heapId: id, rows, box: rows.length === 9 && rows[0]?.length === 9 ? 3 : undefined };
  }
  const isStack = lens.stacks?.includes(name) || (!lens.arrays?.[name] && STACK_NAME.test(bare));
  if (isStack) {
    return {
      kind: "stack", key: `h${id}`, names: [name], heapId: id, container: kind,
      items: obj[1].map((x) => cellOf(x, heap, true)),
      indexInto: lens.indexes?.[name],
    };
  }
  const cfg = lens.arrays?.[name];
  const cells = obj[1].map((x) => cellOf(x, heap, true));
  const numeric = cells.length > 0 && cells.every((c) => c.value !== null);
  return {
    kind: "array", key: `h${id}`, names: [name], heapId: id, container: kind,
    view: cfg?.view ?? (numeric ? "cells" : "cells"),
    cells, pointers: [], truncated: obj[2] ?? undefined,
  };
}

function attachPointers(panels: Panel[], roots: [string, PyVal][], ints: Record<string, number>, ctx: SceneContext) {
  const arrays = panels.filter((p): p is ArrayPanel => p.kind === "array");
  if (!arrays.length) return;
  const lensArrays = ctx.lens.arrays ?? {};
  // The primary array receives heuristic pointers: a lens array if present, else the first parameter that is drawn.
  const primary =
    arrays.find((a) => a.names.some((n) => n in lensArrays && (lensArrays[n].pointers?.length ?? 0) > 0)) ??
    arrays.find((a) => a.names.some((n) => ctx.params.includes(n))) ??
    arrays[0];
  for (const a of arrays) {
    const declared = new Set(a.names.flatMap((n) => lensArrays[n]?.pointers ?? []));
    const guessed = new Set<string>();
    if (a === primary && a.cells.length > 0) for (const [n] of roots) if (POINTER_NAME.test(n) && !declared.has(n)) guessed.add(n);
    for (const name of [...declared, ...guessed]) {
      const v = ints[name];
      if (v === undefined) continue;
      // declared pointers may sit one past the end ("r = len(s)"); guessed ones must point at a cell
      const limit = declared.has(name) ? a.cells.length : a.cells.length - 1;
      if (v >= 0 && v <= limit) a.pointers.push({ name, index: v, tone: toneFor(name) });
    }
    const win = a.names.map((n) => lensArrays[n]?.window).find(Boolean);
    if (win) {
      const lo = evalExpr(win[0], ints);
      const hi = evalExpr(win[1], ints);
      if (lo !== null && hi !== null && hi >= lo && hi >= 0) a.window = [Math.max(0, lo), Math.min(a.cells.length - 1, hi)];
    }
  }
}

function applyIndexes(byName: Map<string, Panel>, heap: Heap, lens: Lens) {
  for (const [holder, target] of Object.entries(lens.indexes ?? {})) {
    const src = byName.get(holder);
    const dst = byName.get(target);
    if (!src || !dst || dst.kind !== "array" || src.heapId === undefined) continue;
    const obj = heap[String(src.heapId)];
    if (!obj || obj[0] === "obj" || obj[0] === "dict") continue;
    // Items are indices - or tuples whose first element is an index, like (start, height).
    const indexOf = (x: PyVal): number | null => {
      if (typeof x === "number") return x;
      const t = deref(heap, x);
      return t && t[0] === "tuple" ? num(t[1][0]) : null;
    };
    dst.marked = { by: holder, indices: obj[1].map(indexOf).filter((x): x is number => x !== null) };
  }
}

function setState<T extends { state: CellState }>(item: T | undefined, state: CellState) {
  if (item && (item.state === "idle" || item.state === "changed")) item.state = state;
}

function applyAccesses(panels: Panel[], byHeap: Map<number, Panel>, byName: Map<string, Panel>, step: Step, prev?: Step) {
  const graph = panels.find((p): p is GraphPanel => p.kind === "graph");
  for (const a of step.a ?? []) {
    if (a.f && graph) {
      const edge = graph.edges.find((e) => e.from === a.o && e.kind === a.f);
      if (edge) edge.state = "new";
      setState(graph.nodes.find((n) => n.id === a.o), "active");
      continue;
    }
    const panel = (a.o !== undefined ? byHeap.get(a.o) : undefined) ?? (a.v ? byName.get(a.v) : undefined) ?? gridRowOwner(panels, a, step.h);
    if (!panel) continue;
    applyAccess(panel, a, step, prev);
  }
}

function gridRowOwner(panels: Panel[], a: Access, heap: Heap): Panel | undefined {
  if (a.o === undefined) return undefined;
  return panels.find((p) => p.kind === "grid" && rowIndex(p, a.o!, heap) >= 0);
}

/** Which row of a grid panel is the list object `rowId`? */
function rowIndex(panel: GridPanel, rowId: number, heap: Heap): number {
  if (panel.heapId === undefined) return -1;
  const obj = heap[String(panel.heapId)];
  if (!obj || obj[0] === "obj" || obj[0] === "dict") return -1;
  return obj[1].findIndex((r) => isRef(r) && r.r === rowId);
}

function modeState(m: Access["m"]): CellState {
  return m === "c" ? "compare" : m === "r" ? "active" : m === "w" ? "changed" : "active";
}

function applyAccess(panel: Panel, a: Access, step: Step, prev?: Step) {
  const hit = a.hit === 1;
  if (panel.kind === "array" || panel.kind === "stack") {
    const cells = panel.kind === "array" ? panel.cells : panel.items;
    if (a.oob && panel.kind === "array") {
      panel.oob = a.i;
      return;
    }
    if (a.m === "push") setState(cells[cells.length - 1], "new");
    else if (a.m === "pushl") setState(cells[0], "new");
    else if (a.m === "pop") {
      const before = prev?.h[String(a.o)];
      const text = before && before[0] !== "obj" && before[0] !== "dict" && a.i !== undefined ? pyRepr(before[1][a.i] as PyVal, prev!.h, 2) : "";
      if (panel.kind === "array") panel.ghost = { index: a.i ?? cells.length, text };
      else panel.ghost = { text, value: null, state: "removed" };
    } else if (a.m === "in") {
      panel.probe = { text: a.kr ?? "?", hit };
      if (hit && a.i !== undefined && a.i >= 0) setState(cells[a.i], "match");
    } else if (a.i !== undefined) setState(cells[a.i], modeState(a.m));
    return;
  }
  if (panel.kind === "map" || panel.kind === "set") {
    const items: { state: CellState }[] = panel.kind === "map" ? panel.entries : panel.items;
    const findByKey = () => (panel.kind === "map" ? panel.entries.findIndex((e) => e.key === a.kr) : panel.items.findIndex((c) => c.text === a.kr));
    if (a.m === "in") {
      panel.probe = { text: a.kr ?? "?", hit };
      if (hit) setState(items[a.ei ?? -1] ?? items[findByKey()], "match");
    } else if (a.m === "w") {
      const i = findByKey();
      setState(items[i], a.ei === -1 || a.ei === undefined ? "new" : "changed");
    } else if (a.m === "del") {
      if (panel.kind === "map") panel.ghost = { key: a.kr ?? "?", value: "" };
    } else if (a.m === "r") {
      if (a.hit === 0) panel.probe = { text: a.kr ?? "?", hit: false };
      else setState(items[a.ei ?? -1] ?? items[findByKey()], "active");
    }
    return;
  }
  if (panel.kind === "grid" && a.o !== undefined && a.i !== undefined) {
    const r = rowIndex(panel, a.o, step.h);
    if (r >= 0) setState(panel.rows[r]?.[a.i], modeState(a.m));
  }
}

function diffPanels(panels: Panel[], step: Step, prev?: Step) {
  if (!prev || step.k === "call") return;
  for (const p of panels) {
    if (p.heapId === undefined) continue;
    const before = prev.h[String(p.heapId)];
    if (!before) {
      if (p.kind === "array") p.cells.forEach((c) => setState(c, "new"));
      continue;
    }
    if (p.kind === "array" || p.kind === "stack") {
      if (before[0] === "obj" || before[0] === "dict") continue;
      const cells = p.kind === "array" ? p.cells : p.items;
      cells.forEach((c, i) => {
        if (i >= before[1].length) setState(c, "new");
        else if (pyRepr(before[1][i] as PyVal, prev.h, 2) !== c.text && c.state === "idle") c.state = "changed";
      });
    } else if (p.kind === "map" && before[0] === "dict") {
      const old = new Map(before[1].map(([k, v]) => [pyRepr(k, prev.h, 2), pyRepr(v, prev.h, 2)]));
      // keys may be shown in a custom format; compare positionally by raw repr when possible
      const raw = step.h[String(p.heapId)];
      if (!raw || raw[0] !== "dict") continue;
      raw[1].forEach(([k, v], i) => {
        const kr = pyRepr(k, step.h, 2);
        const entry = p.entries[i];
        if (!entry) return;
        if (!old.has(kr)) setState(entry, "new");
        else if (old.get(kr) !== pyRepr(v, step.h, 2) && entry.state === "idle") entry.state = "changed";
      });
    } else if (p.kind === "set" && before[0] === "set") {
      const old = new Set(before[1].map((x) => pyRepr(x as PyVal, prev.h, 2)));
      p.items.forEach((c) => {
        if (!old.has(c.text)) setState(c, "new");
      });
    } else if (p.kind === "grid" && before[0] === "list") {
      p.rows.forEach((row, r) => {
        const oldRow = deref(prev.h, before[1][r] as PyVal);
        if (!oldRow || oldRow[0] === "obj" || oldRow[0] === "dict") return;
        row.forEach((c, ci) => {
          if (scalarText(oldRow[1][ci] as PyVal, false) !== c.text && c.state === "idle") c.state = "changed";
        });
      });
    }
  }
}

function diffVars(vars: VarView[], top: Frame | undefined, prev?: Step) {
  if (!prev || !top) return;
  const prevFrame = prev.s.find((f) => f.id === top.id);
  if (!prevFrame) return;
  const old = new Map(prevFrame.v.map(([n, v]) => [n, v]));
  for (const v of vars) {
    if (!old.has(v.name)) v.state = "new";
    else if (scalarText(old.get(v.name)) !== v.text) v.state = "changed";
  }
}

// --------------------------------------------------------------------------- graph

function buildGraphPanel(step: Step, roots: [string, PyVal][], ctx: SceneContext): GraphPanel {
  const heap = step.h;
  const reachable = new Set<number>();
  const queue: PyVal[] = roots.map(([, v]) => v);
  const seen = new Set<number>();
  while (queue.length) {
    const v = queue.shift();
    if (!isRef(v) || seen.has(v.r)) continue;
    seen.add(v.r);
    const obj = heap[String(v.r)];
    if (!obj) continue;
    if (obj[0] === "obj" && isNodeObj(obj)) {
      reachable.add(v.r);
      for (const [, x] of obj[2]) queue.push(x);
    } else if (obj[0] === "dict") {
      for (const [k, x] of obj[1]) queue.push(k, x);
    } else if (obj[0] === "obj") {
      for (const [, x] of obj[2]) queue.push(x);
    } else {
      queue.push(...obj[1]);
    }
  }
  const layout = ctx.graph.flow ? ctx.graph.positionsAt(step) : ctx.graph.positions;
  const varsByNode = new Map<number, string[]>();
  const nulls: string[] = [];
  for (const [name, v] of roots) {
    const short = name.replace(/^self\./, "");
    if (isRef(v) && reachable.has(v.r)) varsByNode.set(v.r, [...(varsByNode.get(v.r) ?? []), short]);
    else if (v === null && NODE_POINTER_NAME.test(short)) nulls.push(short);
  }
  const nodes: GraphNodeView[] = [];
  const edges: GraphEdgeView[] = [];
  let rows = 0;
  let cols = 0;
  for (const id of reachable) {
    const obj = heap[String(id)];
    const pos = layout.get(id) ?? { row: 0, col: 0 };
    rows = Math.max(rows, pos.row + 1);
    cols = Math.max(cols, pos.col + 1);
    const label = field(obj, "key") !== undefined && field(obj, "val") !== undefined
      ? `${scalarText(field(obj, "key"), false)}:${scalarText(field(obj, "val"), false)}`
      : scalarText(field(obj, "val"), false);
    nodes.push({ id, label, cls: obj[0] === "obj" ? obj[1] : "", row: pos.row, col: pos.col, state: "idle", vars: varsByNode.get(id) ?? [] });
    for (const kind of ["next", "prev", "random"] as const) {
      const t = field(obj, kind);
      if (isRef(t) && reachable.has(t.r)) edges.push({ from: id, to: t.r, kind, state: "idle" });
    }
  }
  nodes.sort((a, b) => a.row - b.row || a.col - b.col);
  return { kind: "graph", key: "graph", names: [], nodes, edges, nulls, rows, cols };
}
