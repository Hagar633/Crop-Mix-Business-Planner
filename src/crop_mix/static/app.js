// Crop Mix Planner Frontend Application Logic

// Application State
const state = {
  water_budget: 400000,
  labor_budget: 2500,
  fertilizer_budget: 15000,
  fields: [],
  crops: [],
  ecocropSpecies: [],
  lastResult: null,
};

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  loadPresetData();
  fetchEcoCropSpecies();
});

function initEventListeners() {
  document.getElementById("btn-load-preset").addEventListener("click", loadPresetData);
  document.getElementById("btn-run-optimize").addEventListener("click", runOptimization);
  document.getElementById("btn-add-field").addEventListener("click", () => openFieldModal());
  document.getElementById("btn-add-crop").addEventListener("click", () => openCropModal());
  
  const selectEcoCropHeader = document.getElementById("select-ecocrop-import");
  if (selectEcoCropHeader) {
    selectEcoCropHeader.addEventListener("change", (e) => {
      if (e.target.value) {
        importFromEcoCropHeader(e.target.value);
        e.target.value = "";
      }
    });
  }

  document.getElementById("budget-water").addEventListener("change", (e) => {
    state.water_budget = parseFloat(e.target.value) || 0;
  });
  document.getElementById("budget-labor").addEventListener("change", (e) => {
    state.labor_budget = parseFloat(e.target.value) || 0;
  });
  document.getElementById("budget-fertilizer").addEventListener("change", (e) => {
    state.fertilizer_budget = parseFloat(e.target.value) || 0;
  });
}


// --- API Calls ---

async function loadPresetData() {
  try {
    const res = await fetch("/api/preset");
    if (!res.ok) throw new Error("Failed to load preset data");
    const data = await res.json();

    state.water_budget = data.water_budget;
    state.labor_budget = data.labor_budget;
    state.fertilizer_budget = data.fertilizer_budget;
    state.fields = data.fields;
    state.crops = data.crops;

    document.getElementById("budget-water").value = state.water_budget;
    document.getElementById("budget-labor").value = state.labor_budget;
    document.getElementById("budget-fertilizer").value = state.fertilizer_budget;

    renderFieldsTable();
    renderCropsTable();
    updateTotalLandBadge();
    
    // Automatically run initial optimization
    runOptimization();
  } catch (err) {
    console.error(err);
    alert("Error loading farm dataset presets: " + err.message);
  }
}

async function fetchEcoCropSpecies() {
  try {
    const res = await fetch("/api/ecocrop/crops");
    if (!res.ok) return;
    const species = await res.json();
    state.ecocropSpecies = species;
    populateEcoCropDropdowns(species);
  } catch (err) {
    console.error("Failed to load EcoCrop species list:", err);
  }
}

function populateEcoCropDropdowns(species) {
  const headerSelect = document.getElementById("select-ecocrop-import");
  const modalSelect = document.getElementById("m-ecocrop-select");

  let optionsHtml = '<option value="">Select FAO EcoCrop Species...</option>';
  species.forEach((item) => {
    optionsHtml += `<option value="${escapeHtml(item.name)}">${escapeHtml(item.name)} (${escapeHtml(item.category)} - ${escapeHtml(item.scientific_name)})</option>`;
  });

  if (headerSelect) {
    headerSelect.innerHTML = '<option value="">🌱 Import EcoCrop Species...</option>' + optionsHtml.replace('<option value="">Select FAO EcoCrop Species...</option>', '');
  }
  if (modalSelect) {
    modalSelect.innerHTML = optionsHtml;
  }
}

async function importFromEcoCropHeader(cropName) {
  try {
    const res = await fetch(`/api/ecocrop/lookup/${encodeURIComponent(cropName)}`);
    if (!res.ok) throw new Error(`EcoCrop species '${cropName}' not found.`);
    const item = await res.json();

    // Check if crop already exists
    const existingIdx = state.crops.findIndex(c => c.name.toLowerCase() === item.name.toLowerCase());
    const cropData = {
      name: item.name,
      expected_yield: item.default_expected_yield || 5.0,
      price: item.default_price || 200.0,
      production_cost: item.default_production_cost || 800.0,
      water_requirement: item.water_requirement || 4000.0,
      labor_requirement: 20.0,
      labor_cost_per_hour: 20.0,
      fertilizer_requirement: 100.0,
      fertilizer_cost_per_kg: 1.5,
      soil_requirement: {
        min_ph: item.min_ph,
        max_ph: item.max_ph,
        max_ec: item.max_ec,
        suitable_textures: item.suitable_textures,
      },
    };

    if (existingIdx >= 0) {
      state.crops[existingIdx] = cropData;
    } else {
      state.crops.push(cropData);
    }

    renderCropsTable();
    runOptimization();
  } catch (err) {
    alert("Error importing EcoCrop species: " + err.message);
  }
}

async function autoFillFromEcoCropModal(cropName) {
  if (!cropName) return;
  try {
    const res = await fetch(`/api/ecocrop/lookup/${encodeURIComponent(cropName)}`);
    if (!res.ok) return;
    const item = await res.json();

    document.getElementById("m-crop-name").value = item.name;
    document.getElementById("m-crop-yield").value = item.default_expected_yield || 5.0;
    document.getElementById("m-crop-price").value = item.default_price || 200.0;
    document.getElementById("m-crop-cost").value = item.default_production_cost || 800.0;
    document.getElementById("m-crop-water").value = item.water_requirement || 4000.0;
    document.getElementById("m-crop-min-ph").value = item.min_ph;
    document.getElementById("m-crop-max-ph").value = item.max_ph;
    document.getElementById("m-crop-max-ec").value = item.max_ec;
    document.getElementById("m-crop-textures").value = item.suitable_textures ? item.suitable_textures.join(", ") : "Loam, Clay, Silt";
  } catch (err) {
    console.error("Error auto-filling from EcoCrop:", err);
  }
}


async function runOptimization() {
  const version = document.getElementById("optimizer-version").value;
  const statusPill = document.getElementById("status-pill");
  statusPill.textContent = "Solving LP...";
  statusPill.className = "status-pill";

  const payload = {
    version: version,
    water_budget: parseFloat(document.getElementById("budget-water").value) || 0,
    labor_budget: parseFloat(document.getElementById("budget-labor").value) || 0,
    fertilizer_budget: parseFloat(document.getElementById("budget-fertilizer").value) || 0,
    fields: state.fields,
    crops: state.crops,
  };

  try {
    const res = await fetch("/api/optimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errJson = await res.json();
      throw new Error(errJson.detail || "Optimization failed");
    }

    const result = await res.json();
    state.lastResult = result;
    renderResults(result);

    statusPill.textContent = `Solved (${result.status})`;
    statusPill.className = "status-pill success";
  } catch (err) {
    console.error(err);
    statusPill.textContent = "Error";
    statusPill.className = "status-pill";
    alert("Optimization Error: " + err.message);
  }
}

// --- Render Logic ---

function renderFieldsTable() {
  const tbody = document.getElementById("fields-tbody");
  tbody.innerHTML = "";

  state.fields.forEach((f, idx) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${escapeHtml(f.name)}</strong></td>
      <td>${f.area.toFixed(1)} ha</td>
      <td>${f.ph.toFixed(1)}</td>
      <td>${f.ec.toFixed(1)}</td>
      <td><span class="badge badge-info">${escapeHtml(f.texture)}</span></td>
      <td>${f.organic_matter.toFixed(1)}%</td>
      <td>
        <button class="btn-icon btn-icon-edit" onclick="openFieldModal(${idx})" title="Edit Field">✏️</button>
        <button class="btn-icon" onclick="deleteField(${idx})" title="Delete Field">🗑️</button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  updateTotalLandBadge();
}

function renderCropsTable() {
  const tbody = document.getElementById("crops-tbody");
  tbody.innerHTML = "";

  state.crops.forEach((c, idx) => {
    const rev = c.expected_yield * c.price;
    const laborCost = (c.labor_requirement || 0) * (c.labor_cost_per_hour || 20);
    const fertCost = (c.fertilizer_requirement || 0) * (c.fertilizer_cost_per_kg || 1.5);
    const profit = rev - c.production_cost - laborCost - fertCost;

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${escapeHtml(c.name)}</strong></td>
      <td>${c.expected_yield}</td>
      <td>$${c.price}</td>
      <td>$${c.production_cost}</td>
      <td>${c.water_requirement.toLocaleString()}</td>
      <td>${c.labor_requirement || 0}</td>
      <td>${c.fertilizer_requirement || 0}</td>
      <td style="font-weight:700; color:${profit >= 0 ? '#34d399' : '#f87171'}">$${profit.toFixed(0)}</td>
      <td>
        <button class="btn-icon btn-icon-edit" onclick="openCropModal(${idx})" title="Edit Crop">✏️</button>
        <button class="btn-icon" onclick="deleteCrop(${idx})" title="Delete Crop">🗑️</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function updateTotalLandBadge() {
  const total = state.fields.reduce((sum, f) => sum + f.area, 0);
  document.getElementById("total-land-badge").textContent = `Total Land: ${total.toFixed(1)} ha`;
}

function renderResults(res) {
  // KPI Cards
  document.getElementById("kpi-profit").textContent = `$${res.expected_profit.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
  document.getElementById("kpi-revenue").textContent = `$${res.total_expected_revenue.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
  
  const totalExpenses = res.total_production_cost + res.total_labor_cost + res.total_fertilizer_cost;
  document.getElementById("kpi-expenses").textContent = `$${totalExpenses.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
  document.getElementById("kpi-expenses-sub").textContent = `Prod: $${res.total_production_cost.toFixed(0)} | Labor: $${res.total_labor_cost.toFixed(0)} | Fert: $${res.total_fertilizer_cost.toFixed(0)}`;
  
  document.getElementById("kpi-status").textContent = res.is_feasible ? "Feasible Optimal" : "Infeasible";
  document.getElementById("kpi-solver-name").textContent = `Engine: ${res.version}`;

  // Resource Meters
  renderResourceMeters(res);

  // Suitability Matrix (V3)
  renderSuitabilityMatrix(res);

  // Field Allocations Breakdown
  renderFieldAllocations(res);

  // Binding Constraints
  renderBindingConstraints(res.binding_constraints);
}

function renderResourceMeters(res) {
  const container = document.getElementById("resource-meters-container");
  container.innerHTML = "";

  const resources = [
    { name: "Land Area", used: res.total_land_used, limit: res.field_area_limit, unit: "ha" },
    { name: "Water Budget", used: res.total_water_used, limit: res.water_budget_limit, unit: "m³" },
    { name: "Labor Budget", used: res.total_labor_used, limit: res.labor_budget_limit, unit: "hours" },
    { name: "Fertilizer Budget", used: res.total_fertilizer_used, limit: res.fertilizer_budget_limit, unit: "kg" },
  ];

  resources.forEach((r) => {
    if (r.limit === null || r.limit === undefined || r.limit === Infinity) return;

    const pct = Math.min(100, (r.used / r.limit) * 100);
    let barClass = "";
    if (pct >= 99.5) barClass = "danger";
    else if (pct >= 85) barClass = "warning";

    const box = document.createElement("div");
    box.className = "meter-box";
    box.innerHTML = `
      <div class="meter-header">
        <span>${r.name}</span>
        <span>${pct.toFixed(1)}%</span>
      </div>
      <div class="meter-bar-track">
        <div class="meter-bar-fill ${barClass}" style="width: ${pct}%"></div>
      </div>
      <div class="meter-sub">
        <span>Used: ${r.used.toLocaleString()} ${r.unit}</span>
        <span>Capacity: ${r.limit.toLocaleString()} ${r.unit}</span>
      </div>
    `;
    container.appendChild(box);
  });
}

function renderSuitabilityMatrix(res) {
  const card = document.getElementById("suitability-card");
  const table = document.getElementById("matrix-table");
  
  if (!res.suitability_details || res.suitability_details.length === 0) {
    card.style.display = "none";
    return;
  }
  card.style.display = "block";

  const fields = state.fields.map(f => f.name);
  const crops = state.crops.map(c => c.name);

  // Map details into lookup matrix
  const matrix = {};
  res.suitability_details.forEach((item) => {
    matrix[`${item.field}__${item.crop}`] = item;
  });

  let html = "<thead><tr><th>Field \\ Crop</th>";
  crops.forEach(c => html += `<th>${escapeHtml(c)}</th>`);
  html += "</tr></thead><tbody>";

  fields.forEach(f => {
    html += `<tr><th>${escapeHtml(f)}</th>`;
    crops.forEach(c => {
      const item = matrix[`${f}__${c}`];
      if (item) {
        if (item.suitable) {
          html += `<td class="matrix-cell-suitable" title="Suitable for planting">✅ Suitable</td>`;
        } else {
          html += `<td class="matrix-cell-unsuitable" title="${escapeHtml(item.reason)}">❌ Unsuitable<br><span style="font-size:0.7rem; opacity:0.8">${escapeHtml(item.reason)}</span></td>`;
        }
      } else {
        html += `<td>-</td>`;
      }
    });
    html += "</tr>";
  });
  html += "tbody";

  table.innerHTML = html;
}

function renderFieldAllocations(res) {
  const container = document.getElementById("field-allocations-container");
  container.innerHTML = "";

  if (!res.field_allocations) return;

  Object.entries(res.field_allocations).forEach(([field_name, allocations]) => {
    const card = document.createElement("div");
    card.className = "field-alloc-card";

    let usedHa = 0;
    let itemsHtml = "";

    Object.entries(allocations).forEach(([crop_name, ha]) => {
      if (ha > 0) {
        usedHa += ha;
        const cropObj = state.crops.find(c => c.name === crop_name);
        const profitPerHa = cropObj ? (cropObj.expected_yield * cropObj.price - cropObj.production_cost - (cropObj.labor_requirement||0)*(cropObj.labor_cost_per_hour||20) - (cropObj.fertilizer_requirement||0)*(cropObj.fertilizer_cost_per_kg||1.5)) : 0;
        const profitContrib = ha * profitPerHa;

        itemsHtml += `
          <div class="crop-alloc-item">
            <span>🌾 <strong>${escapeHtml(crop_name)}</strong></span>
            <span>${ha.toFixed(2)} ha &nbsp; (<span style="color:#34d399">+$${profitContrib.toLocaleString('en-US', {minimumFractionDigits:0, maximumFractionDigits:0})}</span>)</span>
          </div>
        `;
      }
    });

    if (!itemsHtml) {
      itemsHtml = `<div class="crop-alloc-item" style="color:var(--text-dim)">* No crops allocated to this field.</div>`;
    }

    const fieldLimit = res.field_land_limits ? res.field_land_limits[field_name] : (state.fields.find(f => f.name === field_name)?.area || 0);

    card.innerHTML = `
      <div class="field-alloc-header">
        <span>📍 ${escapeHtml(field_name)}</span>
        <span style="color:var(--text-muted)">Used: ${usedHa.toFixed(1)} / ${fieldLimit.toFixed(1)} ha</span>
      </div>
      ${itemsHtml}
    `;

    container.appendChild(card);
  });
}

function renderBindingConstraints(constraints) {
  const container = document.getElementById("binding-constraints-container");
  container.innerHTML = "";

  if (!constraints) return;

  constraints.forEach((c) => {
    const item = document.createElement("div");
    item.className = `binding-item ${c.is_binding ? 'is-binding' : ''}`;
    item.innerHTML = `
      <div>
        <strong>${escapeHtml(c.resource)}</strong>
        <div style="font-size:0.8rem; color:var(--text-muted)">Usage: ${c.used.toLocaleString()} / ${c.limit.toLocaleString()} ${c.unit} (${c.utilization_pct}%)</div>
      </div>
      <span class="binding-tag ${c.is_binding ? 'tag-binding' : 'tag-ok'}">
        ${c.is_binding ? '⚠️ Bottleneck Constraint' : '✅ Sufficient'}
      </span>
    `;
    container.appendChild(item);
  });
}

// --- Field CRUD Modals ---

function openFieldModal(idx = null) {
  const modal = document.getElementById("field-modal");
  document.getElementById("field-edit-idx").value = idx !== null ? idx : "";

  if (idx !== null) {
    const f = state.fields[idx];
    document.getElementById("field-modal-title").textContent = "Edit Field";
    document.getElementById("m-field-name").value = f.name;
    document.getElementById("m-field-area").value = f.area;
    document.getElementById("m-field-ph").value = f.ph;
    document.getElementById("m-field-ec").value = f.ec;
    document.getElementById("m-field-texture").value = f.texture;
    document.getElementById("m-field-om").value = f.organic_matter;
  } else {
    document.getElementById("field-modal-title").textContent = "Add New Field";
    document.getElementById("m-field-name").value = `Field_${state.fields.length + 1}`;
    document.getElementById("m-field-area").value = 30.0;
    document.getElementById("m-field-ph").value = 6.8;
    document.getElementById("m-field-ec").value = 1.0;
    document.getElementById("m-field-texture").value = "Loam";
    document.getElementById("m-field-om").value = 2.0;
  }

  modal.classList.add("active");
}

function closeFieldModal() {
  document.getElementById("field-modal").classList.remove("active");
}

function saveFieldModal() {
  const idxStr = document.getElementById("field-edit-idx").value;
  const name = document.getElementById("m-field-name").value.trim();
  const area = parseFloat(document.getElementById("m-field-area").value) || 0;
  const ph = parseFloat(document.getElementById("m-field-ph").value) || 7.0;
  const ec = parseFloat(document.getElementById("m-field-ec").value) || 1.0;
  const texture = document.getElementById("m-field-texture").value;
  const om = parseFloat(document.getElementById("m-field-om").value) || 2.0;

  if (!name || area <= 0) {
    alert("Please provide a valid field name and positive area.");
    return;
  }

  const fieldData = { name, area, ph, ec, texture, organic_matter: om };

  if (idxStr !== "") {
    state.fields[parseInt(idxStr)] = fieldData;
  } else {
    state.fields.push(fieldData);
  }

  closeFieldModal();
  renderFieldsTable();
}

function deleteField(idx) {
  if (confirm(`Are you sure you want to delete field '${state.fields[idx].name}'?`)) {
    state.fields.splice(idx, 1);
    renderFieldsTable();
  }
}

// --- Crop CRUD Modals ---

function openCropModal(idx = null) {
  const modal = document.getElementById("crop-modal");
  document.getElementById("crop-edit-idx").value = idx !== null ? idx : "";

  if (idx !== null) {
    const c = state.crops[idx];
    document.getElementById("crop-modal-title").textContent = "Edit Crop";
    document.getElementById("m-crop-name").value = c.name;
    document.getElementById("m-crop-yield").value = c.expected_yield;
    document.getElementById("m-crop-price").value = c.price;
    document.getElementById("m-crop-cost").value = c.production_cost;
    document.getElementById("m-crop-water").value = c.water_requirement;
    document.getElementById("m-crop-labor").value = c.labor_requirement || 0;
    document.getElementById("m-crop-labor-rate").value = c.labor_cost_per_hour || 20;
    document.getElementById("m-crop-fert").value = c.fertilizer_requirement || 0;
    document.getElementById("m-crop-fert-rate").value = c.fertilizer_cost_per_kg || 1.5;

    const sr = c.soil_requirement;
    document.getElementById("m-crop-min-ph").value = sr ? sr.min_ph : 6.0;
    document.getElementById("m-crop-max-ph").value = sr ? sr.max_ph : 8.0;
    document.getElementById("m-crop-max-ec").value = sr ? sr.max_ec : 2.5;
    document.getElementById("m-crop-textures").value = sr ? sr.suitable_textures.join(", ") : "Loam, Clay, Silt";
  } else {
    document.getElementById("crop-modal-title").textContent = "Add New Crop";
    document.getElementById("m-crop-name").value = `Crop_${state.crops.length + 1}`;
    document.getElementById("m-crop-yield").value = 5.0;
    document.getElementById("m-crop-price").value = 300.0;
    document.getElementById("m-crop-cost").value = 800.0;
    document.getElementById("m-crop-water").value = 4000.0;
    document.getElementById("m-crop-labor").value = 20;
    document.getElementById("m-crop-labor-rate").value = 20;
    document.getElementById("m-crop-fert").value = 150;
    document.getElementById("m-crop-fert-rate").value = 1.5;
    document.getElementById("m-crop-min-ph").value = 6.0;
    document.getElementById("m-crop-max-ph").value = 7.5;
    document.getElementById("m-crop-max-ec").value = 2.0;
    document.getElementById("m-crop-textures").value = "Loam, Clay, Silt, Sandy";
  }

  modal.classList.add("active");
}

function closeCropModal() {
  document.getElementById("crop-modal").classList.remove("active");
}

function saveCropModal() {
  const idxStr = document.getElementById("crop-edit-idx").value;
  const name = document.getElementById("m-crop-name").value.trim();
  const yieldVal = parseFloat(document.getElementById("m-crop-yield").value) || 0;
  const price = parseFloat(document.getElementById("m-crop-price").value) || 0;
  const cost = parseFloat(document.getElementById("m-crop-cost").value) || 0;
  const water = parseFloat(document.getElementById("m-crop-water").value) || 0;
  const labor = parseFloat(document.getElementById("m-crop-labor").value) || 0;
  const laborRate = parseFloat(document.getElementById("m-crop-labor-rate").value) || 20;
  const fert = parseFloat(document.getElementById("m-crop-fert").value) || 0;
  const fertRate = parseFloat(document.getElementById("m-crop-fert-rate").value) || 1.5;

  const minPh = parseFloat(document.getElementById("m-crop-min-ph").value) || 6.0;
  const maxPh = parseFloat(document.getElementById("m-crop-max-ph").value) || 8.0;
  const maxEc = parseFloat(document.getElementById("m-crop-max-ec").value) || 2.5;
  const texturesStr = document.getElementById("m-crop-textures").value;
  const suitableTextures = texturesStr.split(",").map(s => s.trim()).filter(Boolean);

  if (!name || yieldVal <= 0 || price <= 0) {
    alert("Please enter a valid crop name, yield, and market price.");
    return;
  }

  const cropData = {
    name,
    expected_yield: yieldVal,
    price,
    production_cost: cost,
    water_requirement: water,
    labor_requirement: labor,
    labor_cost_per_hour: laborRate,
    fertilizer_requirement: fert,
    fertilizer_cost_per_kg: fertRate,
    soil_requirement: {
      min_ph: minPh,
      max_ph: maxPh,
      max_ec: maxEc,
      suitable_textures: suitableTextures.length > 0 ? suitableTextures : ["Loam", "Clay", "Silt"],
    },
  };

  if (idxStr !== "") {
    state.crops[parseInt(idxStr)] = cropData;
  } else {
    state.crops.push(cropData);
  }

  closeCropModal();
  renderCropsTable();
}

function deleteCrop(idx) {
  if (confirm(`Are you sure you want to delete crop '${state.crops[idx].name}'?`)) {
    state.crops.splice(idx, 1);
    renderCropsTable();
  }
}

// Utility
function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (m) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  }[m]));
}
