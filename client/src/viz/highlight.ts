/** A small, fast Python tokenizer for read-only code panes (the editor uses CodeMirror). */
export type TokenKind = "kw" | "builtin" | "str" | "num" | "com" | "def" | "op" | "self" | "text";

const KEYWORDS = new Set(
  "and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield None True False".split(" "),
);
const BUILTINS = new Set(
  "len range enumerate zip min max sum sorted reversed abs list dict set tuple str int float bool print map filter any all ord chr divmod isinstance heapq deque defaultdict Counter OrderedDict inf ListNode Node List Optional".split(" "),
);

const RE = /(#.*$)|("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')|(\b\d+(?:\.\d+)?\b)|([A-Za-z_][A-Za-z0-9_]*)|(\s+)|(.)/gm;

export function tokenizeLine(line: string): { kind: TokenKind; text: string }[] {
  const out: { kind: TokenKind; text: string }[] = [];
  let prevWord = "";
  RE.lastIndex = 0;
  let m: RegExpExecArray | null;
  while ((m = RE.exec(line))) {
    const [text, com, str, number, word, space] = m;
    if (com) out.push({ kind: "com", text });
    else if (str) out.push({ kind: "str", text });
    else if (number) out.push({ kind: "num", text });
    else if (word) {
      const kind: TokenKind =
        prevWord === "def" || prevWord === "class" ? "def" : KEYWORDS.has(word) ? "kw" : word === "self" ? "self" : BUILTINS.has(word) ? "builtin" : "text";
      out.push({ kind, text });
      prevWord = word;
    } else if (space) out.push({ kind: "text", text });
    else out.push({ kind: "op", text });
    if (!m[0].length) break;
  }
  return out;
}

export const TOKEN_CLASS: Record<TokenKind, string> = {
  kw: "text-violet",
  builtin: "text-sky",
  str: "text-teal",
  num: "text-accent",
  com: "text-faint italic",
  def: "text-accent-strong font-semibold",
  op: "text-muted",
  self: "text-rose/80",
  text: "text-fg",
};
