/**
 * CodeMirror 6, styled from the app's tokens, plus a decoration layer the rest
 * of the app drives: the line the visualizer is on, the error line, a heatmap
 * of how often each line ran, live values at the end of each line (like a
 * debugger), and footnotes from analyzers - a numbered marker on the line and,
 * for the main finding, a note set directly under it (the Footnote Law).
 */
import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import { Compartment, EditorState, RangeSetBuilder, StateEffect, StateField, type Extension } from "@codemirror/state";
import {
  Decoration, EditorView, WidgetType, crosshairCursor, drawSelection, dropCursor, highlightActiveLine,
  highlightActiveLineGutter, keymap, lineNumbers, rectangularSelection, type DecorationSet,
} from "@codemirror/view";
import { defaultKeymap, history, historyKeymap, indentWithTab } from "@codemirror/commands";
import { python } from "@codemirror/lang-python";
import { HighlightStyle, bracketMatching, indentOnInput, indentUnit, syntaxHighlighting } from "@codemirror/language";
import { autocompletion, closeBrackets, closeBracketsKeymap, completionKeymap } from "@codemirror/autocomplete";
import { highlightSelectionMatches, searchKeymap } from "@codemirror/search";
import { tags as t } from "@lezer/highlight";
import { vim } from "@replit/codemirror-vim";

/** A finding pinned under its line. Actions come back through `onFootnoteAction(id)`. */
export interface EditorFootnote {
  line: number;
  n: number;
  title: string;
  body: string;
  actions?: { id: string; label: string }[];
}

export interface EditorMarks {
  line?: number;
  next?: number;
  errorLine?: number;
  heat?: Record<number, number>;
  notes?: { line: number; n: number }[];
  /** Text shown after the end of a line: `{7: "l = 1"}`. */
  values?: Record<number, string>;
  footnote?: EditorFootnote;
}

export interface CodeEditorHandle {
  focus: () => void;
  setValue: (v: string) => void;
  getValue: () => string;
}

interface Props {
  value: string;
  onChange?: (v: string) => void;
  onRun?: () => void;
  onSubmit?: () => void;
  onVisualize?: () => void;
  onFootnoteAction?: (id: string) => void;
  marks?: EditorMarks;
  fontSize?: number;
  vimMode?: boolean;
  className?: string;
}

const highlight = HighlightStyle.define([
  { tag: [t.keyword, t.controlKeyword, t.operatorKeyword, t.definitionKeyword, t.moduleKeyword], color: "var(--note)" },
  { tag: [t.string, t.special(t.string)], color: "var(--ref)" },
  { tag: [t.number, t.bool, t.null], color: "var(--accent)" },
  { tag: t.comment, color: "var(--text-faint)", fontStyle: "italic" },
  { tag: [t.function(t.definition(t.variableName)), t.definition(t.className)], color: "var(--accent-strong)", fontWeight: "600" },
  { tag: [t.function(t.variableName), t.function(t.propertyName)], color: "var(--sky)" },
  { tag: [t.className, t.typeName], color: "var(--sky)" },
  { tag: t.self, color: "var(--text-muted)", fontStyle: "italic" },
  { tag: [t.operator, t.punctuation, t.bracket], color: "var(--text-muted)" },
  { tag: t.propertyName, color: "var(--text)" },
  { tag: t.variableName, color: "var(--text)" },
]);

const baseTheme = EditorView.theme({
  "&": { height: "100%", backgroundColor: "var(--bg-elev)", color: "var(--text)" },
  ".cm-scroller": { fontFamily: "var(--font-mono)", lineHeight: "1.7" },
  ".cm-content": { caretColor: "var(--accent)", padding: "10px 0" },
  ".cm-gutters": { backgroundColor: "var(--bg-elev)", color: "var(--text-faint)", border: "none", paddingLeft: "6px" },
  ".cm-activeLineGutter": { backgroundColor: "transparent", color: "var(--text-muted)" },
  ".cm-activeLine": { backgroundColor: "color-mix(in oklab, var(--text) 3.5%, transparent)" },
  ".cm-cursor, .cm-dropCursor": { borderLeftColor: "var(--accent)", borderLeftWidth: "2px" },
  "&.cm-focused .cm-selectionBackground, .cm-selectionBackground, ::selection": { backgroundColor: "color-mix(in oklab, var(--accent) 22%, transparent) !important" },
  ".cm-selectionMatch": { backgroundColor: "color-mix(in oklab, var(--accent) 12%, transparent)" },
  ".cm-matchingBracket": { backgroundColor: "color-mix(in oklab, var(--ref) 20%, transparent)", outline: "none" },
  ".cm-tooltip": { backgroundColor: "var(--bg-elev-2)", border: "1px solid var(--border-strong)", borderRadius: "10px", overflow: "hidden" },
  ".cm-tooltip-autocomplete > ul > li[aria-selected]": { backgroundColor: "var(--accent-soft)", color: "var(--text)" },
  ".cm-panels": { backgroundColor: "var(--bg-elev-2)", color: "var(--text)" },
  ".cm-trace-line": { backgroundColor: "var(--accent-soft) !important", boxShadow: "inset 3px 0 0 var(--accent)" },
  ".cm-trace-next": { boxShadow: "inset 2px 0 0 color-mix(in oklab, var(--accent) 45%, transparent)" },
  ".cm-error-line": { backgroundColor: "var(--warn-soft) !important", boxShadow: "inset 3px 0 0 var(--warn)" },
  ".cm-footnote": { color: "var(--accent)", fontSize: "10px", fontWeight: "700", verticalAlign: "super", marginLeft: "6px", cursor: "help" },
  ".cm-heat-label": { color: "var(--accent-strong)", fontSize: "10px", marginLeft: "10px", fontStyle: "italic" },
  ".cm-inline-value": { color: "var(--text-faint)", fontStyle: "italic", marginLeft: "18px", fontSize: "0.9em", whiteSpace: "pre" },
  ".cm-trace-line .cm-inline-value": { color: "var(--accent-strong)" },
  ".cm-line-footnote": {
    // A capped width: CodeMirror sizes its content to max-content, so an unwrapped note would widen it.
    maxWidth: "min(580px, 78vw)", margin: "6px 14px 8px 4px", padding: "10px 12px", borderRadius: "9px", fontFamily: "var(--font-sans)",
    fontSize: "13px", lineHeight: "1.5", whiteSpace: "normal", color: "var(--text-muted)", backgroundColor: "var(--bg-elev-2)",
    border: "1px solid color-mix(in oklab, var(--warn) 55%, transparent)", boxShadow: "0 0 28px -16px var(--warn)",
  },
  ".cm-line-footnote-head": { display: "flex", alignItems: "baseline", gap: "8px", color: "var(--text)", fontWeight: "600", fontSize: "13.5px" },
  ".cm-line-footnote-n": { fontFamily: "var(--font-mono)", fontSize: "10.5px", fontWeight: "700", color: "var(--warn)" },
  ".cm-line-footnote p": { margin: "4px 0 0" },
  ".cm-line-footnote-actions": { display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "8px" },
  ".cm-line-footnote button": {
    font: "inherit", fontSize: "12px", fontWeight: "600", padding: "3px 10px", borderRadius: "6px", cursor: "pointer",
    border: "1px solid var(--border-strong)", backgroundColor: "transparent", color: "var(--text)",
  },
  ".cm-line-footnote button:first-child": { borderColor: "color-mix(in oklab, var(--warn) 60%, transparent)", color: "var(--warn)", backgroundColor: "var(--warn-soft)" },
  ".cm-line-footnote button:focus-visible": { outline: "2px solid var(--accent)", outlineOffset: "2px" },
});

const setMarks = StateEffect.define<EditorMarks>();

class NoteWidget extends WidgetType {
  constructor(readonly n: number) {
    super();
  }
  toDOM() {
    const el = document.createElement("span");
    el.className = "cm-footnote";
    el.textContent = String(this.n);
    return el;
  }
  eq(other: NoteWidget) {
    return other.n === this.n;
  }
}

class HeatWidget extends WidgetType {
  constructor(readonly hits: number) {
    super();
  }
  toDOM() {
    const el = document.createElement("span");
    el.className = "cm-heat-label";
    el.textContent = `×${this.hits >= 10_000 ? `${Math.round(this.hits / 1000)}K` : this.hits}`;
    return el;
  }
  eq(other: HeatWidget) {
    return other.hits === this.hits;
  }
}

class ValueWidget extends WidgetType {
  constructor(readonly text: string) {
    super();
  }
  toDOM() {
    const el = document.createElement("span");
    el.className = "cm-inline-value";
    el.textContent = this.text;
    return el;
  }
  eq(other: ValueWidget) {
    return other.text === this.text;
  }
}

/** Fired on the editor DOM when a footnote action button is clicked; the component relays it. */
const FOOTNOTE_EVENT = "fc-footnote-action";

class FootnoteWidget extends WidgetType {
  constructor(readonly note: EditorFootnote) {
    super();
  }
  toDOM(view: EditorView) {
    const box = document.createElement("div");
    box.className = "cm-line-footnote";
    box.setAttribute("role", "note");
    const head = document.createElement("div");
    head.className = "cm-line-footnote-head";
    const n = document.createElement("span");
    n.className = "cm-line-footnote-n";
    n.textContent = String(this.note.n);
    const title = document.createElement("span");
    title.textContent = this.note.title;
    head.append(n, title);
    const body = document.createElement("p");
    body.textContent = this.note.body;
    box.append(head, body);
    if (this.note.actions?.length) {
      const row = document.createElement("div");
      row.className = "cm-line-footnote-actions";
      for (const a of this.note.actions) {
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = a.label;
        b.addEventListener("mousedown", (e) => e.preventDefault()); // don't move the cursor
        b.addEventListener("click", () => view.dom.dispatchEvent(new CustomEvent(FOOTNOTE_EVENT, { detail: a.id })));
        row.append(b);
      }
      box.append(row);
    }
    return box;
  }
  eq(other: FootnoteWidget) {
    return JSON.stringify(other.note) === JSON.stringify(this.note);
  }
  ignoreEvent() {
    return true;
  }
}

function buildDecorations(state: EditorState, m: EditorMarks): DecorationSet {
  const builder = new RangeSetBuilder<Decoration>();
  const lines = state.doc.lines;
  const maxHeat = m.heat ? Math.max(1, ...Object.values(m.heat)) : 1;
  for (let ln = 1; ln <= lines; ln++) {
    const line = state.doc.line(ln);
    const classes: string[] = [];
    let style = "";
    if (ln === m.line) classes.push("cm-trace-line");
    else if (ln === m.next) classes.push("cm-trace-next");
    if (ln === m.errorLine) classes.push("cm-error-line");
    const hits = m.heat?.[ln];
    if (hits && ln !== m.line) {
      const pct = Math.round(6 + (hits / maxHeat) * 26);
      style = `background-color: color-mix(in oklab, var(--accent) ${pct}%, transparent)`;
    }
    if (classes.length || style) builder.add(line.from, line.from, Decoration.line({ class: classes.join(" "), attributes: style ? { style } : {} }));
    // Same position, increasing side: inline widgets first, then the block note under the line.
    const widgets: Decoration[] = [];
    if (hits) widgets.push(Decoration.widget({ widget: new HeatWidget(hits), side: 1 }));
    for (const note of m.notes ?? []) if (note.line === ln) widgets.push(Decoration.widget({ widget: new NoteWidget(note.n), side: 2 }));
    if (m.footnote?.line === ln) widgets.push(Decoration.widget({ widget: new NoteWidget(m.footnote.n), side: 2 }));
    const value = m.values?.[ln];
    if (value) widgets.push(Decoration.widget({ widget: new ValueWidget(value), side: 3 }));
    if (m.footnote?.line === ln) widgets.push(Decoration.widget({ widget: new FootnoteWidget(m.footnote), block: true, side: 1 }));
    for (const w of widgets) builder.add(line.to, line.to, w);
  }
  return builder.finish();
}

const marksField = StateField.define<{ marks: EditorMarks; deco: DecorationSet }>({
  create: (state) => ({ marks: {}, deco: buildDecorations(state, {}) }),
  update(value, tr) {
    let marks = value.marks;
    let changed = false;
    for (const e of tr.effects) {
      if (e.is(setMarks)) {
        marks = e.value;
        changed = true;
      }
    }
    if (tr.docChanged && (marks.line || marks.errorLine || marks.heat || marks.notes || marks.values || marks.footnote)) {
      marks = {}; // edits invalidate trace/analysis marks
      changed = true;
    }
    return changed ? { marks, deco: buildDecorations(tr.state, marks) } : value;
  },
  provide: (f) => EditorView.decorations.from(f, (v) => v.deco),
});

export const CodeEditor = forwardRef<CodeEditorHandle, Props>(function CodeEditor(
  { value, onChange, onRun, onSubmit, onVisualize, onFootnoteAction, marks, fontSize = 14, vimMode = false, className },
  ref,
) {
  const host = useRef<HTMLDivElement>(null);
  const view = useRef<EditorView | null>(null);
  const handlers = useRef({ onChange, onRun, onSubmit, onVisualize, onFootnoteAction });
  handlers.current = { onChange, onRun, onSubmit, onVisualize, onFootnoteAction };
  const vimComp = useRef(new Compartment());
  const sizeComp = useRef(new Compartment());

  useEffect(() => {
    const runKeys = keymap.of([
      { key: "Mod-Enter", run: () => (handlers.current.onRun?.(), true) },
      { key: "Mod-Shift-Enter", run: () => (handlers.current.onSubmit?.(), true) },
      { key: "Mod-.", run: () => (handlers.current.onVisualize?.(), true) },
    ]);
    const extensions: Extension[] = [
      vimComp.current.of(vimMode ? vim() : []),
      runKeys,
      lineNumbers(),
      highlightActiveLineGutter(),
      history(),
      drawSelection(),
      dropCursor(),
      EditorState.allowMultipleSelections.of(true),
      indentOnInput(),
      indentUnit.of("    "),
      EditorState.tabSize.of(4),
      syntaxHighlighting(highlight),
      bracketMatching(),
      closeBrackets(),
      autocompletion(),
      rectangularSelection(),
      crosshairCursor(),
      highlightActiveLine(),
      highlightSelectionMatches(),
      keymap.of([...closeBracketsKeymap, ...defaultKeymap, ...searchKeymap, ...historyKeymap, ...completionKeymap, indentWithTab]),
      python(),
      baseTheme,
      sizeComp.current.of(EditorView.theme({ "&": { fontSize: `${fontSize}px` } })),
      marksField,
      EditorView.updateListener.of((u) => {
        if (u.docChanged) handlers.current.onChange?.(u.state.doc.toString());
      }),
    ];
    const v = new EditorView({ state: EditorState.create({ doc: value, extensions }), parent: host.current! });
    view.current = v;
    const onAction = (e: Event) => handlers.current.onFootnoteAction?.((e as CustomEvent<string>).detail);
    v.dom.addEventListener(FOOTNOTE_EVENT, onAction);
    return () => {
      v.dom.removeEventListener(FOOTNOTE_EVENT, onAction);
      v.destroy();
      view.current = null;
    };
    // The editor is created once; value/settings changes are pushed in below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    view.current?.dispatch({ effects: vimComp.current.reconfigure(vimMode ? vim() : []) });
  }, [vimMode]);

  useEffect(() => {
    view.current?.dispatch({ effects: sizeComp.current.reconfigure(EditorView.theme({ "&": { fontSize: `${fontSize}px` } })) });
  }, [fontSize]);

  useEffect(() => {
    view.current?.dispatch({ effects: setMarks.of(marks ?? {}) });
    const focus = marks?.line ?? marks?.footnote?.line;
    if (focus && view.current) {
      const doc = view.current.state.doc;
      if (focus <= doc.lines) {
        view.current.dispatch({ effects: EditorView.scrollIntoView(doc.line(focus).from, { y: "nearest" }) });
      }
    }
  }, [marks]);

  useImperativeHandle(ref, () => ({
    focus: () => view.current?.focus(),
    getValue: () => view.current?.state.doc.toString() ?? "",
    setValue: (v: string) => {
      const cur = view.current;
      if (!cur || cur.state.doc.toString() === v) return;
      cur.dispatch({ changes: { from: 0, to: cur.state.doc.length, insert: v } });
    },
  }));

  return <div ref={host} className={className} />;
});
