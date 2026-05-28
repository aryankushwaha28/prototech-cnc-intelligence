const form = document.querySelector("#uploadForm");
const pill = document.querySelector("#statusPill");
const quoteBox = document.querySelector("#quoteBox");
const featureBox = document.querySelector("#featureBox");
const downloads = document.querySelector("#downloads");
const gcodeBox = document.querySelector("#gcodeBox");
const preview = document.querySelector("#preview");
const toolpathCanvas = document.querySelector("#toolpathCanvas");
const toolpathStats = document.querySelector("#toolpathStats");
const fitToolpath = document.querySelector("#fitToolpath");
let currentGcode = "";
let currentToolpath = null;

function setStatus(text) {
  pill.textContent = text;
}

function drawPreview(job) {
  preview.innerHTML = "";
  const features = job.features;
  const bbox = job.geometry_summary?.bounding_box;
  if (!features || !bbox) return;
  const width = Math.max(bbox.max_x - bbox.min_x, 1);
  const height = Math.max(bbox.max_y - bbox.min_y, 1);
  const sx = 540 / width;
  const sy = 300 / height;
  const scale = Math.min(sx, sy);
  const tx = 30 - bbox.min_x * scale;
  const ty = 330 + bbox.min_y * scale;
  const map = (p) => `${(p.x * scale + tx).toFixed(2)},${(ty - p.y * scale).toFixed(2)}`;

  for (const contour of [...features.contours, ...features.open_profiles]) {
    if (!contour.vertices.length) continue;
    const points = contour.vertices.map(map).join(" ");
    const shape = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
    shape.setAttribute("points", points);
    shape.setAttribute("fill", contour.is_outer_profile ? "rgba(15,118,110,0.08)" : "none");
    shape.setAttribute("stroke", contour.is_outer_profile ? "#0f766e" : "#334155");
    shape.setAttribute("stroke-width", "2");
    if (contour.is_outer_profile) shape.setAttribute("closed", "true");
    preview.appendChild(shape);
  }

  for (const hole of features.holes) {
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", (hole.center.x * scale + tx).toFixed(2));
    circle.setAttribute("cy", (ty - hole.center.y * scale).toFixed(2));
    circle.setAttribute("r", Math.max((hole.diameter_mm / 2) * scale, 3).toFixed(2));
    circle.setAttribute("fill", "rgba(180,83,9,0.16)");
    circle.setAttribute("stroke", "#b45309");
    circle.setAttribute("stroke-width", "2");
    preview.appendChild(circle);
  }
}

function renderJob(job) {
  setStatus(job.status);
  if (job.status === "failed") {
    quoteBox.textContent = job.error || "Pipeline failed.";
    return;
  }
  if (!job.quote) return;
  const c = job.quote.cost_breakdown;
  quoteBox.innerHTML = `INR ${c.total_for_quantity_inr.toLocaleString()} <small>/ USD ${c.total_usd}</small>`;
  featureBox.innerHTML = `
    <table>
      <tr><th>Feature</th><th>Count</th></tr>
      <tr><td>Holes</td><td>${job.features.holes.length}</td></tr>
      <tr><td>Contours</td><td>${job.features.contours.length}</td></tr>
      <tr><td>Pockets</td><td>${job.features.pockets.length}</td></tr>
      <tr><td>Radii</td><td>${job.features.radii.length}</td></tr>
      <tr><td>Complexity</td><td>${job.features.complexity_score}</td></tr>
    </table>`;
  downloads.innerHTML = `
    <a href="/api/jobs/${job.job_id}/quote.pdf">Download PDF Quote</a>
    <a href="/api/jobs/${job.job_id}/program.nc">Download G-code .nc</a>
    <button type="button" data-action="copy-gcode">Copy G-code</button>`;
  drawPreview(job);
}

async function poll(jobId) {
  const res = await fetch(`/api/jobs/${jobId}`);
  const job = await res.json();
  renderJob(job);
  if (job.status !== "complete" && job.status !== "failed") {
    window.setTimeout(() => poll(jobId), 700);
  } else if (job.status === "complete") {
    const nc = await fetch(`/api/jobs/${jobId}/program.nc`);
    currentGcode = await nc.text();
    gcodeBox.textContent = currentGcode;
    currentToolpath = parseGcode(currentGcode);
    drawToolpath(currentToolpath);
  }
}

downloads.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;
  const action = target.dataset.action;
  if (action !== "copy-gcode") return;
  if (!currentGcode) {
    currentGcode = gcodeBox.textContent || "";
  }
  const copied = await copyText(currentGcode);
  target.textContent = copied ? "Copied G-code" : "Copy failed";
  window.setTimeout(() => {
    target.textContent = "Copy G-code";
  }, 1400);
});

async function copyText(text) {
  if (!text || text.startsWith("(")) return false;
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    // Some browser contexts block clipboard writes; use the textarea fallback below.
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";
  textarea.style.top = "0";
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  try {
    return document.execCommand("copy");
  } finally {
    document.body.removeChild(textarea);
  }
}

function parseWords(line) {
  const words = {};
  for (const match of line.matchAll(/([A-Z])([-+]?\d*\.?\d+)/g)) {
    words[match[1]] = Number.parseFloat(match[2]);
  }
  return words;
}

function cleanGcodeLine(line) {
  return line
    .replace(/\([^)]*\)/g, "")
    .replace(/;.*/g, "")
    .trim()
    .toUpperCase();
}

function arcPoints(start, end, center, clockwise) {
  const startAngle = Math.atan2(start.y - center.y, start.x - center.x);
  let endAngle = Math.atan2(end.y - center.y, end.x - center.x);
  let sweep = endAngle - startAngle;
  if (clockwise && sweep >= 0) sweep -= Math.PI * 2;
  if (!clockwise && sweep <= 0) sweep += Math.PI * 2;
  const radius = Math.hypot(start.x - center.x, start.y - center.y);
  const steps = Math.max(12, Math.ceil(Math.abs(sweep) / (Math.PI / 18)));
  const points = [];
  for (let index = 1; index <= steps; index += 1) {
    const angle = startAngle + (sweep * index) / steps;
    points.push({ x: center.x + Math.cos(angle) * radius, y: center.y + Math.sin(angle) * radius });
  }
  points[points.length - 1] = end;
  return points;
}

function parseGcode(text) {
  const segments = [];
  const drills = [];
  let modal = "G00";
  let position = { x: 0, y: 0, z: 0 };

  for (const rawLine of text.split(/\r?\n/)) {
    const line = cleanGcodeLine(rawLine);
    if (!line || line === "%") continue;

    const codes = [...line.matchAll(/G0?(\d+)/g)].map((match) => `G${match[1].padStart(2, "0")}`);
    const motion = codes.find((code) => ["G00", "G01", "G02", "G03", "G81"].includes(code));
    if (motion) modal = motion;

    const words = parseWords(line);
    const next = {
      x: Number.isFinite(words.X) ? words.X : position.x,
      y: Number.isFinite(words.Y) ? words.Y : position.y,
      z: Number.isFinite(words.Z) ? words.Z : position.z,
    };

    if (modal === "G81" && (Number.isFinite(words.X) || Number.isFinite(words.Y))) {
      drills.push({ x: next.x, y: next.y, z: next.z });
      position = next;
      continue;
    }

    if (!Number.isFinite(words.X) && !Number.isFinite(words.Y)) {
      position = next;
      continue;
    }

    if (modal === "G02" || modal === "G03") {
      const center = {
        x: position.x + (Number.isFinite(words.I) ? words.I : 0),
        y: position.y + (Number.isFinite(words.J) ? words.J : 0),
      };
      segments.push({
        type: modal === "G02" ? "arc-cw" : "arc-ccw",
        points: [position, ...arcPoints(position, next, center, modal === "G02")],
      });
    } else {
      segments.push({
        type: modal === "G00" ? "rapid" : "cut",
        points: [position, next],
      });
    }
    position = next;
  }

  return { segments, drills };
}

function toolpathBounds(toolpath) {
  const points = [];
  for (const segment of toolpath.segments) points.push(...segment.points);
  points.push(...toolpath.drills);
  if (!points.length) return null;
  return {
    minX: Math.min(...points.map((point) => point.x)),
    maxX: Math.max(...points.map((point) => point.x)),
    minY: Math.min(...points.map((point) => point.y)),
    maxY: Math.max(...points.map((point) => point.y)),
  };
}

function drawGrid(ctx, width, height) {
  ctx.fillStyle = "#0f172a";
  ctx.fillRect(0, 0, width, height);
  ctx.strokeStyle = "rgba(148, 163, 184, 0.16)";
  ctx.lineWidth = 1;
  for (let x = 0; x <= width; x += 48) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
    ctx.stroke();
  }
  for (let y = 0; y <= height; y += 48) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }
}

function drawEmptyToolpath() {
  if (!(toolpathCanvas instanceof HTMLCanvasElement)) return;
  const rect = toolpathCanvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  toolpathCanvas.width = Math.max(1, Math.floor(rect.width * dpr));
  toolpathCanvas.height = Math.max(1, Math.floor(rect.height * dpr));
  const ctx = toolpathCanvas.getContext("2d");
  if (!ctx) return;
  ctx.scale(dpr, dpr);
  drawGrid(ctx, rect.width, rect.height);
}

function drawToolpath(toolpath) {
  if (!(toolpathCanvas instanceof HTMLCanvasElement)) return;
  const rect = toolpathCanvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  toolpathCanvas.width = Math.max(1, Math.floor(rect.width * dpr));
  toolpathCanvas.height = Math.max(1, Math.floor(rect.height * dpr));
  const ctx = toolpathCanvas.getContext("2d");
  if (!ctx) return;
  ctx.scale(dpr, dpr);
  const width = rect.width;
  const height = rect.height;
  drawGrid(ctx, width, height);

  const bounds = toolpathBounds(toolpath);
  if (!bounds) {
    toolpathStats.textContent = "No XY motion found in generated G-code.";
    return;
  }

  const padding = 34;
  const spanX = Math.max(bounds.maxX - bounds.minX, 1);
  const spanY = Math.max(bounds.maxY - bounds.minY, 1);
  const scale = Math.min((width - padding * 2) / spanX, (height - padding * 2) / spanY);
  const map = (point) => ({
    x: padding + (point.x - bounds.minX) * scale,
    y: height - padding - (point.y - bounds.minY) * scale,
  });

  for (const segment of toolpath.segments) {
    const isRapid = segment.type === "rapid";
    ctx.beginPath();
    segment.points.forEach((point, index) => {
      const mapped = map(point);
      if (index === 0) ctx.moveTo(mapped.x, mapped.y);
      else ctx.lineTo(mapped.x, mapped.y);
    });
    ctx.strokeStyle = isRapid ? "rgba(148, 163, 184, 0.55)" : "#34d399";
    ctx.lineWidth = isRapid ? 1 : 2;
    ctx.setLineDash(isRapid ? [6, 5] : []);
    ctx.stroke();
  }
  ctx.setLineDash([]);

  for (const drill of toolpath.drills) {
    const mapped = map(drill);
    ctx.beginPath();
    ctx.arc(mapped.x, mapped.y, 4, 0, Math.PI * 2);
    ctx.fillStyle = "#f59e0b";
    ctx.fill();
  }

  const cutCount = toolpath.segments.filter((segment) => segment.type !== "rapid").length;
  const rapidCount = toolpath.segments.length - cutCount;
  toolpathStats.innerHTML = `
    <strong>${toolpath.segments.length.toLocaleString()} moves</strong>
    Cut moves: ${cutCount.toLocaleString()}<br>
    Rapid moves: ${rapidCount.toLocaleString()}<br>
    Drill cycles: ${toolpath.drills.length.toLocaleString()}<br>
    X span: ${spanX.toFixed(2)} mm<br>
    Y span: ${spanY.toFixed(2)} mm`;
}

fitToolpath.addEventListener("click", () => {
  if (currentToolpath) drawToolpath(currentToolpath);
});

window.addEventListener("resize", () => {
  if (currentToolpath) drawToolpath(currentToolpath);
  else drawEmptyToolpath();
});

drawEmptyToolpath();

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus("Uploading");
  quoteBox.textContent = "Running pipeline...";
  featureBox.textContent = "Parsing DXF...";
  downloads.innerHTML = "";
  currentGcode = "";
  currentToolpath = null;
  gcodeBox.textContent = "(waiting for generated .nc)";
  toolpathStats.textContent = "Waiting for G-code.";
  preview.innerHTML = "";

  const data = new FormData(form);
  data.set("use_ai", form.elements.use_ai.checked ? "true" : "false");
  const res = await fetch("/api/jobs", { method: "POST", body: data });
  if (!res.ok) {
    const err = await res.json();
    setStatus("Error");
    quoteBox.textContent = err.detail?.message || "Upload failed.";
    return;
  }
  const accepted = await res.json();
  poll(accepted.job_id);
});
