/**
 * Evaluates the tiny expressions lenses use for window bounds, e.g. "r - k + 1".
 * Only identifiers, integers, + and - : no eval(), nothing to inject.
 */
export function evalExpr(expr: string, vars: Record<string, number>): number | null {
  const tokens = expr.match(/[A-Za-z_][A-Za-z0-9_]*|\d+|[+-]/g);
  if (!tokens || tokens.join("") !== expr.replace(/\s+/g, "")) return null;
  let total = 0;
  let sign = 1;
  let expectTerm = true;
  for (const t of tokens) {
    if (t === "+" || t === "-") {
      if (expectTerm) {
        if (t === "-") sign = -sign;
        continue;
      }
      sign = t === "-" ? -1 : 1;
      expectTerm = true;
      continue;
    }
    const value = /^\d+$/.test(t) ? Number(t) : vars[t];
    if (value === undefined || !Number.isFinite(value)) return null;
    total += sign * value;
    sign = 1;
    expectTerm = false;
  }
  return expectTerm ? null : total;
}
