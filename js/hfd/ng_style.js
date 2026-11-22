// One stylesheet for the NG nodes. Colours come from ComfyUI's own variables so it follows the theme.

const CSS = `
.hfd-plan { box-sizing: border-box; width: 100%; font: 12px/1.45 var(--font-inter, system-ui, sans-serif); color: var(--input-text, #ddd);
  background: var(--comfy-input-bg, #222); border: 1px solid var(--border-color, #444); border-radius: 6px; padding: 8px; overflow: auto; }
.hfd-plan h4 { margin: 0 0 4px; font-size: 12px; font-weight: 600; }
.hfd-plan .hfd-summary { display: flex; flex-wrap: wrap; gap: 6px 12px; margin-bottom: 6px; }
.hfd-plan .hfd-pill { padding: 1px 8px; border-radius: 10px; background: var(--comfy-menu-bg, #353535); }
.hfd-plan .hfd-error { color: #ff7b72; white-space: pre-wrap; }
.hfd-plan ul { margin: 0 0 6px; padding-left: 16px; }
.hfd-plan li.hfd-issue { color: #e3b341; }
.hfd-plan details { margin: 2px 0; border-top: 1px solid var(--border-color, #444); padding-top: 2px; }
.hfd-plan summary { cursor: pointer; }
.hfd-plan .hfd-dim { opacity: .65; }
.hfd-plan pre { margin: 4px 0; white-space: pre-wrap; font: 11px/1.4 var(--font-mono, monospace); }
.hfd-plan .hfd-bar { display: flex; height: 8px; margin: 4px 0 8px; border-radius: 4px; overflow: hidden; background: var(--comfy-menu-bg, #353535); }
.hfd-plan .hfd-seg { height: 100%; border-right: 1px solid var(--comfy-input-bg, #222); }
.hfd-card { box-sizing: border-box; width: 100%; padding: 8px; overflow: auto; font: 12px/1.4 system-ui; color: var(--input-text, #ddd); background: var(--comfy-input-bg, #222); border-radius: 6px; }
.hfd-card .hfd-tools { display: flex; gap: 5px; flex-wrap: wrap; margin: 6px 0; }
.hfd-card button, .hfd-card input, .hfd-card select { font: inherit; color: inherit; background: var(--comfy-menu-bg, #353535); border: 1px solid var(--border-color, #555); border-radius: 4px; padding: 4px 6px; max-width: 100%; }
.hfd-card button { cursor: pointer; }
.hfd-card button:disabled { opacity: .5; cursor: default; }
.hfd-card .hfd-status { white-space: pre-wrap; }
.hfd-card .hfd-thumbnail { max-width: 100%; max-height: 110px; object-fit: contain; display: block; margin: auto; }
.hfd-card .hfd-waveform { width: 100%; height: 48px; }
.hfd-card .hfd-media-preview { white-space: pre-wrap; max-height: 130px; overflow: auto; }
.hfd-card label { display: flex; gap: 6px; align-items: center; margin: 3px 0; }
.hfd-card .hfd-suggestion { white-space: pre-wrap; border-left: 2px solid #b294db; padding: 6px; margin: 4px 0; }
.hfd-assistbar { display: flex; gap: 6px; margin-bottom: 6px; }
.hfd-assistbar button { padding: 3px 8px; border-radius: 4px; cursor: pointer; }
.hfd-assistbar button[aria-pressed=true] { background: #2f5d8c; color: white; }
`;

let injected = false;

export function ensureStyle() {
  if (injected) return;
  const tag = document.createElement("style");
  tag.textContent = CSS;
  document.head.appendChild(tag);
  injected = true;
}
