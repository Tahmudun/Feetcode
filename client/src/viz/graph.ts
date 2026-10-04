/**
 * Where to draw linked-list nodes.
 *
 * Stable layout (default): a node's position is decided the first time it
 * appears and never changes. Reversing a list then shows arrows flipping while
 * nodes stay put - which is exactly the thing to learn. Rules, applied in
 * discovery order (variables first, then container contents):
 *   - a node whose predecessor (x.next == node) is placed goes right after it;
 *   - else a node whose successor is placed goes right before it;
 *   - else, in the first step with nodes, each chain gets its own row
 *     (list1 on row 0, list2 on row 1);
 *   - later unrelated nodes (copies, results, dummies) share one "new" row,
 *     in creation order - so copied nodes line up under their originals.
 *
 * Flow layout (doubly linked lists, e.g. LRU cache): recomputed every step by
 * following next pointers, so reordering a node visibly slides it.
 */
import type { Heap, PyVal, Step, Trace } from "@/runtime/types";
import { field, isNodeObj, isRef } from "./decode";

export interface Pos {
  row: number;
  col: number;
}

export interface GraphLayout {
  flow: boolean;
  positions: Map<number, Pos>;
  positionsAt: (step: Step) => Map<number, Pos>;
}

function nextOf(heap: Heap, id: number): number | null {
  const v = field(heap[String(id)], "next");
  return isRef(v) && isNodeObj(heap[String(v.r)]) ? v.r : null;
}

/** Node ids in the order a reader meets them: node variables first, then nodes inside containers. */
function discover(step: Step): number[] {
  const heap = step.h;
  const out: number[] = [];
  const seen = new Set<number>();
  const visitChain = (start: number) => {
    let cur: number | null = start;
    while (cur !== null && !seen.has(cur)) {
      seen.add(cur);
      out.push(cur);
      cur = nextOf(heap, cur);
    }
  };
  const direct: number[] = [];
  const nested: PyVal[] = [];
  for (const frame of step.s) {
    for (const [name, v] of frame.v) {
      if (!isRef(v)) continue;
      const obj = heap[String(v.r)];
      if (!obj) continue;
      if (isNodeObj(obj)) direct.push(v.r);
      else if (name === "self" && obj[0] === "obj") {
        for (const [, fv] of obj[2]) {
          const fo = isRef(fv) ? heap[String(fv.r)] : undefined;
          if (fo && isNodeObj(fo)) direct.push((fv as { r: number }).r);
          else nested.push(fv);
        }
      } else nested.push(v);
    }
  }
  direct.forEach(visitChain);
  // breadth-first through containers for the rest
  const queue = [...nested];
  const seenObj = new Set<number>();
  while (queue.length) {
    const v = queue.shift();
    if (!isRef(v) || seenObj.has(v.r)) continue;
    seenObj.add(v.r);
    const obj = heap[String(v.r)];
    if (!obj) continue;
    if (isNodeObj(obj)) visitChain(v.r);
    else if (obj[0] === "dict") obj[1].forEach(([k, x]) => queue.push(k, x));
    else if (obj[0] === "obj") obj[2].forEach(([, x]) => queue.push(x));
    else queue.push(...obj[1]);
  }
  // random pointers can reach nodes no chain did
  for (const id of [...out]) {
    const r = field(heap[String(id)], "random");
    if (isRef(r) && isNodeObj(heap[String(r.r)]) && !seen.has(r.r)) visitChain(r.r);
  }
  return out;
}

class Placer {
  positions = new Map<number, Pos>();
  private taken = new Set<string>();
  private rowCount = 0;
  private newRow = -1;
  private nextCol = new Map<number, number>();

  private free(p: Pos) {
    return !this.taken.has(`${p.row}:${p.col}`);
  }
  private put(id: number, p: Pos) {
    this.positions.set(id, p);
    this.taken.add(`${p.row}:${p.col}`);
    this.nextCol.set(p.row, Math.max(this.nextCol.get(p.row) ?? 0, p.col + 1));
  }

  place(step: Step, ids: number[], firstStep: boolean) {
    const heap = step.h;
    const pred = new Map<number, number>();
    for (const id of ids) {
      const n = nextOf(heap, id);
      if (n !== null && !pred.has(n)) pred.set(n, id);
    }
    for (const id of ids) {
      if (this.positions.has(id)) continue;
      const p = pred.get(id);
      const pp = p !== undefined ? this.positions.get(p) : undefined;
      if (pp && this.free({ row: pp.row, col: pp.col + 1 })) {
        this.put(id, { row: pp.row, col: pp.col + 1 });
        continue;
      }
      const s = nextOf(heap, id);
      const sp = s !== null ? this.positions.get(s) : undefined;
      if (sp && this.free({ row: sp.row, col: sp.col - 1 })) {
        this.put(id, { row: sp.row, col: sp.col - 1 });
        continue;
      }
      if (firstStep) {
        const row = this.rowCount++;
        this.put(id, { row, col: 0 });
        continue;
      }
      if (this.newRow < 0) this.newRow = this.rowCount++;
      this.put(id, { row: this.newRow, col: this.nextCol.get(this.newRow) ?? 0 });
    }
  }

  normalized(): Map<number, Pos> {
    let minCol = 0;
    for (const p of this.positions.values()) minCol = Math.min(minCol, p.col);
    const out = new Map<number, Pos>();
    for (const [id, p] of this.positions) out.set(id, { row: p.row, col: p.col - minCol });
    return out;
  }
}

function hasPrevPointers(trace: Trace): boolean {
  for (const step of trace.steps) {
    for (const obj of Object.values(step.h)) {
      if (obj[0] === "obj" && obj[2].some(([k]) => k === "prev")) return true;
    }
  }
  return false;
}

export function layoutGraph(trace: Trace): GraphLayout {
  const flow = hasPrevPointers(trace);
  const placer = new Placer();
  let first = true;
  for (const step of trace.steps) {
    const ids = discover(step);
    if (!ids.length) continue;
    placer.place(step, ids, first);
    first = false;
  }
  const positions = placer.normalized();
  const cache = new WeakMap<Step, Map<number, Pos>>();
  return {
    flow,
    positions,
    positionsAt(step: Step) {
      let p = cache.get(step);
      if (!p) {
        const local = new Placer();
        local.place(step, discover(step), true);
        p = local.normalized();
        cache.set(step, p);
      }
      return p;
    },
  };
}
