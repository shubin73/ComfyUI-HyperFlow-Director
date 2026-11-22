// The Text card's body: the note, quick inserts, role and templates. The `text` widget is what the Director reads:
// as Scene it is story (AI: split into shots reads it like the Prompt), in any other role it goes into every part.
import { h } from "./h3s_dom.js";
import { INSERTS, TEMPLATES } from "./h3c_model.js";
import { usageBox, ownerBox, suggestionBox } from "./h3c_parts.js";

export const CHARACTER_LIMIT = 2000;

export function textBody(S, actions) {
  const text = S.values.text || "", story = S.usage === "scene";
  const editor = h("textarea", { class: "hfd-c-in hfd-c-editor", rows: 9, value: text, spellcheck: false, "aria-label": "Note",
    placeholder: "A story, a rule or a look, in any language. [character] marks a part to fill in; @Name points at a connected Context.",
    oninput: (event) => actions.setNote(event.target.value) });
  S.els.editor = editor;
  const template = h("select", { class: "hfd-c-in", style: { flex: "1 1 auto" }, "aria-label": "Template" },
    Object.keys(TEMPLATES).map((name) => h("option", { value: name }, name)));
  return [
    h("div", { class: "hfd-c-grid", style: { gridTemplateColumns: "minmax(0,1.5fr) minmax(0,1fr)" } },
      h("div", { class: "hfd-c-box" },
        h("div", { class: "hfd-c-cap" }, story ? "Story · the AI splits it into shots" : "Note · goes into every render part", h("span", { class: "hfd-c-grow" }),
          h("span", { class: text.length > CHARACTER_LIMIT ? "hfd-c-lbl hfd-c-warn" : "hfd-c-lbl", style: { textTransform: "none" } }, `${text.length} / ${CHARACTER_LIMIT}`)),
        editor,
        h("span", { class: "hfd-c-hint" }, story ? "Lyrics belong on the song's Audio card: there each line is timed and sung in its render part."
          : "Any language. Final prompts per render part are written in the Studio.")),
      h("div", { class: "hfd-c-box" }, h("div", { class: "hfd-c-cap" }, "Quick insert"),
        INSERTS.map(([key, label, color]) => h("button", { class: "hfd-c-ins", style: { borderColor: `${color}66`, color }, onclick: () => actions.insert(key) }, `+ ${label}`)))),
    h("div", { class: "hfd-c-grid", style: { gridTemplateColumns: "minmax(0,1fr) minmax(0,1fr)" } }, usageBox(S, actions, 2),
      h("div", { class: "hfd-c-grid" },
        h("div", { class: "hfd-c-box" }, h("div", { class: "hfd-c-cap" }, "Templates"),
          h("div", { class: "hfd-c-row", style: { flexWrap: "nowrap" } }, template,
            h("button", { class: "hfd-c-btn", onclick: () => actions.useTemplate(template.value) }, "Use"))),
        ownerBox(S, actions, "A rule for the whole project. Link it to a figure to scope it to that figure."))),
    suggestionBox(S, actions),
  ].filter(Boolean);
}
