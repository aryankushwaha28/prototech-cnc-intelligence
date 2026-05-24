const form = document.querySelector("#uploadForm");
const pill = document.querySelector("#statusPill");
const quoteBox = document.querySelector("#quoteBox");
const featureBox = document.querySelector("#featureBox");
const downloads = document.querySelector("#downloads");
const gcodeBox = document.querySelector("#gcodeBox");
const preview = document.querySelector("#preview");

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
    <a href="/api/jobs/${job.job_id}/program.nc">Download G-code .nc</a>`;
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
    gcodeBox.textContent = await nc.text();
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus("Uploading");
  quoteBox.textContent = "Running pipeline...";
  featureBox.textContent = "Parsing DXF...";
  downloads.innerHTML = "";
  gcodeBox.textContent = "(waiting for generated .nc)";
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
