// Draws the plan the server computed. Pure rendering: it never talks to the server and keeps no state.

const SEGMENT_COLORS = ["#4f9cf9", "#e08b3c", "#7bc47f", "#c58af9", "#f06a8d", "#4fc1c1"];

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function seconds(value) {
  return `${value.toFixed(2)} s`;
}

function summary(data) {
  const row = el("div", "hfd-summary");
  row.append(el("span", "hfd-pill", `${data.chunks.length} chunk${data.chunks.length === 1 ? "" : "s"}`),
             el("span", "hfd-pill", `${seconds(data.total_s)} (${data.total_frames} frames)`),
             el("span", "hfd-pill", data.mode));
  return row;
}

function timeline(data) {
  const bar = el("div", "hfd-bar");
  data.chunks.forEach((chunk, index) => {
    const segment = el("div", "hfd-seg");
    segment.style.flex = String(chunk.delivered_frames);
    segment.style.background = SEGMENT_COLORS[index % SEGMENT_COLORS.length];
    segment.title = `chunk ${index + 1}: ${seconds(chunk.start_s)} - ${seconds(chunk.end_s)}`;
    bar.append(segment);
  });
  return bar;
}

function issues(list) {
  if (!list.length) return null;
  const block = el("div");
  block.append(el("h4", "", `Notes (${list.length})`));
  const items = el("ul");
  for (const issue of list) items.append(el("li", "hfd-issue", issue.ref ? `${issue.ref}: ${issue.text}` : issue.text));
  block.append(items);
  return block;
}

function refList(refs) {
  const groups = {};
  for (const ref of refs) (groups[ref.kind] ||= []).push(ref.name);
  return Object.entries(groups).map(([kind, names]) => `${kind}: ${names.join(", ")}`).join("  ·  ");
}

function chunkRow(chunk) {
  const row = el("details");
  const head = `chunk ${chunk.index + 1}  ${seconds(chunk.start_s)} - ${seconds(chunk.end_s)}`;
  const detail = chunk.head_frames ? `  (sampled ${chunk.sampled_frames}, head ${chunk.head_frames})` : "";
  row.append(el("summary", "", head), el("div", "hfd-dim", `${chunk.delivered_frames} frames${detail}, ${chunk.mode}, ${chunk.refs.length} reference(s)`));
  if (chunk.refs.length) row.append(el("div", "hfd-dim", refList(chunk.refs)));
  row.append(el("pre", "hfd-compiled-prompt", chunk.prompt));
  return row;
}

export function renderPlan(root, data) {
  root.replaceChildren();
  if (!data) {
    root.append(el("div", "hfd-dim", "planning…"));
    return;
  }
  if (!data.ok) {
    root.append(el("div", "hfd-error", data.error));
    return;
  }
  root.append(summary(data), timeline(data));
  const problems = issues(data.issues);
  if (problems) root.append(problems);
  const chunks = el("div", "hfd-chunks");
  chunks.append(el("h4", "", "Chunks"));
  data.chunks.forEach((chunk) => chunks.append(chunkRow(chunk)));
  root.append(chunks);
}
