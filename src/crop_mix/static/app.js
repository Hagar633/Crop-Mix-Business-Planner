// Crop Mix Planner Frontend Application Logic - Egyptian Farmer Edition (Bilingual & EGP)

// Application State
const state = {
  lang: "ar", // Default language: Arabic
  water_budget: 400000,
  labor_budget: 2500,
  fertilizer_budget: 15000,
  fields: [],
  crops: [],
  ecocropSpecies: [],
  rotationCrops: [],
  lastResult: null,
};

// Bilingual Translation Dictionary
const i18nData = {
  ar: {
    "landing.brandSub": "المنظومة الذكية للتخطيط الزراعي والدورة الزراعية",
    "nav.goOptimizer": "الانتقال للمخطط 🚀",
    "landing.heroTag": "صُمم خصيصاً للمزارع المصري",
    "landing.heroTitle": "احسب أرباح مزرعتك بالجنيه المصري، وخطط لدورتك الزراعية بأعلى كفاءة",
    "landing.heroSub": "برنامج ذكي يحدد أفضل توزيع للمحاصيل على أراضيك لزيادة الأرباح الصافية (EGP)، مع ترشيد مياه الري والسماد، وتطبيق قواعد الدورة الزراعية الرسمية وملائمة التربة.",
    "landing.startBtn": "ابدأ تخطيط مزرعتك الآن",
    "landing.learnMore": "تعرّف على الميزات",
    "features.title": "لماذا يستعين المزارع ببرنامج CropMix؟",
    "features.sub": "أدوات متكاملة تناسب الفلاح المصري للوصول لأعلى إنتاجية وأفضل عائد مالي",
    "features.f1Title": "قواعد الدورة الزراعية المصرية",
    "features.f1Desc": "يفحص تتابع المحاصيل تلقائياً لمنع التتابع الضار (مثل زراعة الطماطم بعد البطاطس) ويحمي التربة من الإجهاد وفقاً للجدول الزمني الموصى به.",
    "features.f2Title": "ترشيد مياه الري والأرباح بالجنيه",
    "features.f2Desc": "يحسب تكاليف الإنتاج، العمالة، والأسمدة بالجنيه المصري (EGP) ويوزّع الأراضي بناءً على حصة المياه المتاحة لتحقيق أعلى صافي ربح.",
    "features.f3Title": "ملائمة التربة لكل قطعة أرض",
    "features.f3Desc": "يطابق درجة الحموضة (pH)، ملوحة التربة (EC)، ونوع التربة (طينية، رملية، صفراء) لضمان زراعة المحصول المناسب في الأرض المناسبة.",
    "landing.bottomBannerTitle": "جاهز لحساب التوزيع الأمثل لمزرعتك؟",
    "landing.bottomBannerSub": "ادخل بيانات أرضك والمحاصيل المتاحة وسيقوم المحرك الرياضي بحساب أفضل خطة زراعية في ثوانٍ",
    "footer.text": "برنامج مخطط المحاصيل الزراعية والدورة الزراعية بمصر • CropMix Business Planner",
    "nav.home": "الرئيسية",
    "opt.headerTagline": "حاسبة التخطيط الزراعي والدورة الزراعية",
    "opt.engineLabel": "محرك التخطيط:",
    "opt.loadPreset": "تحميل مزرعة افتراضية",
    "opt.runOptimize": "احسب التوزيع الأمثل",
    "step1.title": "الخطوة 1: ميزانية المزرعة العامة",
    "step1.sub": "حدد كمية المياه والعمالة والأسمدة المتاحة لمزرعتك بالكامل",
    "step1.waterLabel": "إجمالي ميزانية المياه",
    "step1.laborLabel": "إجمالي ساعات العمل",
    "step1.fertLabel": "إجمالي سماد المزرعة",
    "step2.title": "الخطوة 2: أراضي المزرعة والمحصول السابق",
    "step2.sub": "حدد مساحة كل أرض، نوع التربة، والزرعة السابقة بالدورة الزراعية",
    "step2.addField": "+ إضافة أرض جديدة",
    "step3.title": "الخطوة 3: المحاصيل والأسعار بالجنيه المصري (EGP)",
    "step3.sub": "حدد الإنتاجية المتوقعة، سعر البيع، والتكلفة لكل محصول بالجنيه المصري",
    "step3.ecocropDefault": "🌱 استيراد من موسوعة فاو إيكوكروب...",
    "step3.addCrop": "+ إضافة محصول",
    "th.fieldName": "اسم الأرض",
    "th.fieldArea": "المساحة (هكتار/فدان)",
    "th.ph": "الحموضة pH",
    "th.ec": "الملوحة EC",
    "th.texture": "نوع التربة",
    "th.om": "المادة العضوية %",
    "th.prevCrop": "المحصول السابق",
    "th.action": "إجراء",
    "th.crop": "المحصول",
    "th.yield": "الإنتاجية (طن/هكتار)",
    "th.price": "سعر الطن (EGP)",
    "th.cost": "التكلفة (EGP)",
    "th.water": "المياه (م³/هكتار)",
    "th.labor": "العمالة (ساعة)",
    "th.fert": "السماد (كجم)",
    "th.netProfit": "الربح الصافي (EGP)",
    "res.title": "نتائج التخطيط وتوزيع المحاصيل على الأرض",
    "kpi.profit": "إجمالي الربح الصافي المتوقع",
    "kpi.profitSub": "الربح الصافي بالجنيه المصري (EGP)",
    "kpi.revenue": "إجمالي الإيرادات المتوقعة",
    "kpi.revenueSub": "قيمة بيع المحاصيل الإجمالية",
    "kpi.expenses": "إجمالي التكاليف والمصروفات",
    "kpi.status": "حالة الحل البرمجي",
    "res.resourceTitle": "نسبة استهلاك ميزانية المزرعة والموارد",
    "res.rotationTitle": "مصفوفة الدورة الزراعية المصرية لكل أرض (V4)",
    "res.rotationSub": "تقييم المحصول السابق وتجنب التتابع الضار حسب الجدول الرسمي لـ 53 محصولاً",
    "res.soilTitle": "مصفوفة ملائمة التربة والأرض للمحاصيل",
    "res.soilSub": "فحص درجات الحموضة (pH)، الملوحة (EC)، ونوع التربة المناسب",
    "res.allocTitle": "توزيع الزراعة الأمثل لكل قطعة أرض (هكتار/فدان)",
    "res.bindingTitle": "محلل القيود المحددة للربح (الموارد المنتهية)",
    "res.bindingSub": "يحدد المورد الذي استُهلك بنسبة 100% ومنع زيادة الربح",
    "modal.fieldName": "اسم قطعة الأرض",
    "modal.fieldArea": "المساحة (هكتار / فدان)",
    "modal.ph": "حموضة التربة (pH)",
    "modal.ec": "ملوحة التربة (EC dS/m)",
    "modal.texture": "نوع التربة",
    "modal.om": "المادة العضوية %",
    "modal.prevCrop": "المحصول السابق (سجل الدورة الزراعية V4)",
    "modal.ecocropAuto": "🌱 استيراد متطلبات التربة والمياه تلقائياً من موسوعة فاو إيكوكروب",
    "modal.cropName": "اسم المحصول",
    "modal.yield": "الإنتاجية المتوقعة (طن/هكتار)",
    "modal.price": "سعر بيع الطن بالجنيه (EGP/ton)",
    "modal.cost": "تكلفة الزراعة بالجنيه (EGP/ha)",
    "modal.water": "احتياج المياه (م³/هكتار)",
    "modal.labor": "احتياج العمالة (ساعة/هكتار)",
    "modal.laborRate": "أجرة ساعة العمل (EGP/ساعة)",
    "modal.fert": "احتياج السماد (كجم/هكتار)",
    "modal.fertRate": "سعر كيلو السماد (EGP/كجم)",
    "modal.soilLimitsTitle": "شروط ملائمة التربة (V3)",
    "modal.minPh": "أقل درجة حموضة تحمل",
    "modal.maxPh": "أعلى درجة حموضة تحمل",
    "modal.maxEc": "أقصى ملوحة متحملة (EC dS/m)",
    "modal.textures": "أنواع التربة المناسبة (مفصولة بفواصل)",
    "btn.cancel": "إلغاء",
    "btn.save": "حفظ البيانات",
  },
  en: {
    "landing.brandSub": "Smart Agricultural Crop & Rotation Planner",
    "nav.goOptimizer": "Go to Optimizer 🚀",
    "landing.heroTag": "Tailored for Egyptian Farmers",
    "landing.heroTitle": "Maximize Your Farm Profits in EGP & Plan Ideal Crop Rotations",
    "landing.heroSub": "Smart optimization tool that allocates crops to fields to maximize net profit in Egyptian Pounds (EGP), optimizes water and fertilizer, and enforces official rotation rules.",
    "landing.startBtn": "Start Farm Planning Now",
    "landing.learnMore": "Learn More Features",
    "features.title": "Why Farmers Trust CropMix?",
    "features.sub": "Integrated tools designed for Egyptian agriculture to maximize yields and financial returns.",
    "features.f1Title": "Egyptian Crop Rotation Rules",
    "features.f1Desc": "Automatically evaluates 53 crop successions to prevent harmful sequences (e.g. Tomato after Potato) and preserve soil fertility.",
    "features.f2Title": "Water & EGP Profit Optimization",
    "features.f2Desc": "Calculates production, labor, and fertilizer costs in Egyptian Pounds (EGP) and optimizes land use within water availability limits.",
    "features.f3Title": "Field Soil Chemistry Suitability",
    "features.f3Desc": "Matches pH, EC salinity, and soil texture (Clay, Loam, Sandy) to ensure each crop is planted in suitable soil.",
    "landing.bottomBannerTitle": "Ready to Optimize Your Farm Plan?",
    "landing.bottomBannerSub": "Input your field measurements and crop parameters to calculate optimal profit in seconds.",
    "footer.text": "Egyptian Agricultural Crop & Rotation Planner • CropMix Business Planner",
    "nav.home": "Home",
    "opt.headerTagline": "Farm Crop & Rotation Calculator",
    "opt.engineLabel": "Optimizer Engine:",
    "opt.loadPreset": "Load Default Farm",
    "opt.runOptimize": "Solve Optimal Plan",
    "step1.title": "Step 1: Global Farm Budgets",
    "step1.sub": "Set water, labor, and fertilizer availability across your farm",
    "step1.waterLabel": "Total Water Budget",
    "step1.laborLabel": "Total Labor Hours",
    "step1.fertLabel": "Total Fertilizer Budget",
    "step2.title": "Step 2: Farm Fields & Rotation History",
    "step2.sub": "Manage field boundaries, soil chemistry, and previous crop planted",
    "step2.addField": "+ Add New Field",
    "step3.title": "Step 3: Crop Catalog & Prices (EGP)",
    "step3.sub": "Configure expected yield, price, and costs per hectare in EGP",
    "step3.ecocropDefault": "🌱 Import from FAO EcoCrop DB...",
    "step3.addCrop": "+ Add New Crop",
    "th.fieldName": "Field Name",
    "th.fieldArea": "Area (ha/feddan)",
    "th.ph": "pH",
    "th.ec": "Salinity EC",
    "th.texture": "Soil Texture",
    "th.om": "Organic %",
    "th.prevCrop": "Previous Crop",
    "th.action": "Action",
    "th.crop": "Crop",
    "th.yield": "Yield (t/ha)",
    "th.price": "Price (EGP/t)",
    "th.cost": "Cost (EGP/ha)",
    "th.water": "Water (m³/ha)",
    "th.labor": "Labor (h/ha)",
    "th.fert": "Fert. (kg/ha)",
    "th.netProfit": "Net Profit (EGP)",
    "res.title": "Optimization Results & Field Plan",
    "kpi.profit": "Expected Net Profit",
    "kpi.profitSub": "Net profit in Egyptian Pounds (EGP)",
    "kpi.revenue": "Expected Gross Revenue",
    "kpi.revenueSub": "Total expected crop sales",
    "kpi.expenses": "Total Expenses & Costs",
    "kpi.status": "Solver Status",
    "res.resourceTitle": "Resource Capacity & Budget Utilization",
    "res.rotationTitle": "Field × Crop Rotation Suitability Matrix (V4)",
    "res.rotationSub": "Evaluates previous crop succession against 53 Egyptian rotation rules",
    "res.soilTitle": "Field × Crop Soil Suitability Matrix",
    "res.soilSub": "Evaluates pH, salinity EC, and texture compatibility",
    "res.allocTitle": "Optimal Land Allocation by Field (Hectares)",
    "res.bindingTitle": "Binding Bottleneck Constraints Analyzer",
    "res.bindingSub": "Identifies resources at 100% capacity restricting profit",
    "modal.fieldName": "Field Name",
    "modal.fieldArea": "Area (hectares/feddans)",
    "modal.ph": "Soil pH",
    "modal.ec": "Salinity EC (dS/m)",
    "modal.texture": "Soil Texture",
    "modal.om": "Organic Matter %",
    "modal.prevCrop": "Previous Crop (V4 Rotation History)",
    "modal.ecocropAuto": "🌱 Auto-fill Soil & Water Requirements from FAO EcoCrop DB",
    "modal.cropName": "Crop Name",
    "modal.yield": "Expected Yield (t/ha)",
    "modal.price": "Price per ton (EGP/ton)",
    "modal.cost": "Production Cost (EGP/ha)",
    "modal.water": "Water Req (m³/ha)",
    "modal.labor": "Labor Req (hours/ha)",
    "modal.laborRate": "Labor Rate (EGP/hour)",
    "modal.fert": "Fertilizer Req (kg/ha)",
    "modal.fertRate": "Fertilizer Rate (EGP/kg)",
    "modal.soilLimitsTitle": "Soil Suitability Limits (V3)",
    "modal.minPh": "Min Tolerable pH",
    "modal.maxPh": "Max Tolerable pH",
    "modal.maxEc": "Max Salinity EC",
    "modal.textures": "Suitable Textures (comma separated)",
    "btn.cancel": "Cancel",
    "btn.save": "Save Data",
  }
};

// Crop translation mapping for common crop names
const cropNamesAr = {
  "Wheat": "قمح (Wheat)",
  "Yellow Corn": "ذرة صفراء (Yellow Corn)",
  "Soybean": "فول صويا (Soybean)",
  "Tomato": "طماطم (Tomato)",
  "Cotton": "قطن (Cotton)",
  "Barley": "شعير (Barley)",
  "Rice": "أرز (Rice)",
  "Potato": "بطاطس (Potato)",
  "Onion": "بصل (Onion)",
  "Garlic": "ثوم (Garlic)",
  "Alfalfa": "برسيم (Alfalfa)",
  "Sugar Cane": "قصب السكر (Sugar Cane)",
};

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  applyLanguage(state.lang);
  loadPresetData();
  fetchEcoCropSpecies();
  fetchRotationCrops();
});

// SPA Navigation
function navigateTo(pageId) {
  document.querySelectorAll(".page-view").forEach((view) => {
    view.classList.remove("active");
  });
  const target = document.getElementById(`page-${pageId}`);
  if (target) {
    target.classList.add("active");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

function scrollToSection(sectionId) {
  const elem = document.getElementById(sectionId);
  if (elem) {
    elem.scrollIntoView({ behavior: "smooth" });
  }
}

// Language Toggle
function toggleLanguage() {
  state.lang = state.lang === "ar" ? "en" : "ar";
  applyLanguage(state.lang);
}

function applyLanguage(lang) {
  const html = document.documentElement;
  html.setAttribute("lang", lang);
  html.setAttribute("dir", lang === "ar" ? "rtl" : "ltr");

  const langToggleText = lang === "ar" ? "English" : "العربية";
  const landingBtnText = document.getElementById("lang-text-landing");
  const optBtnText = document.getElementById("lang-text-opt");

  if (landingBtnText) landingBtnText.textContent = langToggleText;
  if (optBtnText) optBtnText.textContent = langToggleText;

  // Translate data-i18n elements
  const dict = i18nData[lang] || i18nData.ar;
  document.querySelectorAll("[data-i18n]").forEach((elem) => {
    const key = elem.getAttribute("data-i18n");
    if (dict[key]) {
      elem.textContent = dict[key];
    }
  });

  renderFieldsTable();
  renderCropsTable();
  if (state.lastResult) {
    renderResults(state.lastResult);
  }
}

function getCurrencySymbol() {
  return state.lang === "ar" ? "ج.م" : "EGP";
}

function getCropDisplayName(name) {
  if (state.lang === "ar" && cropNamesAr[name]) {
    return cropNamesAr[name];
  }
  return name;
}

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
    
    runOptimization();
  } catch (err) {
    console.error(err);
    alert(state.lang === "ar" ? "خطأ في تحميل المزرعة الافتراضية: " + err.message : "Error loading preset farm: " + err.message);
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

async function fetchRotationCrops() {
  try {
    const res = await fetch("/api/rotation/matrix");
    if (!res.ok) return;
    const data = await res.json();
    state.rotationCrops = data.crops || [];
  } catch (err) {
    console.error("Failed to load rotation matrix crops:", err);
  }
}

function populatePreviousCropDropdown(selectedVal = "") {
  const select = document.getElementById("m-field-prev-crop");
  if (!select) return;

  const noneLabel = state.lang === "ar" ? "لا يوجد / أرض بور (None)" : "None (Fallow / New Field)";
  let html = `<option value="">${noneLabel}</option>`;
  state.rotationCrops.forEach((c) => {
    const sel = c === selectedVal ? ' selected' : '';
    const disp = getCropDisplayName(c);
    html += `<option value="${escapeHtml(c)}"${sel}>${escapeHtml(disp)}</option>`;
  });

  if (selectedVal && !state.rotationCrops.includes(selectedVal)) {
    const disp = getCropDisplayName(selectedVal);
    html += `<option value="${escapeHtml(selectedVal)}" selected>${escapeHtml(disp)}</option>`;
  }

  select.innerHTML = html;
}

function populateEcoCropDropdowns(species) {
  const headerSelect = document.getElementById("select-ecocrop-import");
  const modalSelect = document.getElementById("m-ecocrop-select");

  const defaultMsg = state.lang === "ar" ? "اختر نوع المحصول من قائمة فاو إيكوكروب..." : "Select FAO EcoCrop Species...";
  const importMsg = state.lang === "ar" ? "🌱 استيراد من موسوعة فاو إيكوكروب..." : "🌱 Import EcoCrop Species...";

  let optionsHtml = `<option value="">${defaultMsg}</option>`;
  species.forEach((item) => {
    optionsHtml += `<option value="${escapeHtml(item.name)}">${escapeHtml(item.name)} (${escapeHtml(item.category)} - ${escapeHtml(item.scientific_name)})</option>`;
  });

  if (headerSelect) {
    headerSelect.innerHTML = `<option value="">${importMsg}</option>` + optionsHtml.replace(`<option value="">${defaultMsg}</option>`, '');
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

    const existingIdx = state.crops.findIndex(c => c.name.toLowerCase() === item.name.toLowerCase());
    const cropData = {
      name: item.name,
      expected_yield: item.default_expected_yield || 5.0,
      price: item.default_price || 12000.0,
      production_cost: item.default_production_cost || 20000.0,
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
    document.getElementById("m-crop-price").value = item.default_price || 12000.0;
    document.getElementById("m-crop-cost").value = item.default_production_cost || 20000.0;
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
  
  statusPill.textContent = state.lang === "ar" ? "جاري الحساب..." : "Solving LP...";
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

    statusPill.textContent = state.lang === "ar" ? `تم الحل (${result.status})` : `Solved (${result.status})`;
    statusPill.className = "status-pill success";
  } catch (err) {
    console.error(err);
    statusPill.textContent = state.lang === "ar" ? "خطأ" : "Error";
    statusPill.className = "status-pill";
    alert((state.lang === "ar" ? "خطأ في إجراء الحساب: " : "Optimization Error: ") + err.message);
  }
}

// --- Render Logic ---

function renderFieldsTable() {
  const tbody = document.getElementById("fields-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  const haUnit = state.lang === "ar" ? "هكتار/فدان" : "ha";
  const noneText = state.lang === "ar" ? "لا يوجد" : "None";

  state.fields.forEach((f, idx) => {
    const prevCrop = f.previous_crop ? getCropDisplayName(f.previous_crop) : noneText;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${escapeHtml(f.name)}</strong></td>
      <td>${f.area.toFixed(1)} ${haUnit}</td>
      <td>${f.ph.toFixed(1)}</td>
      <td>${f.ec.toFixed(1)}</td>
      <td><span class="badge badge-info">${escapeHtml(f.texture)}</span></td>
      <td>${f.organic_matter.toFixed(1)}%</td>
      <td><span class="badge badge-secondary" style="background: rgba(99, 102, 241, 0.15); color: #818cf8;">${escapeHtml(prevCrop)}</span></td>
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
  if (!tbody) return;
  tbody.innerHTML = "";

  const curr = getCurrencySymbol();

  state.crops.forEach((c, idx) => {
    const rev = c.expected_yield * c.price;
    const laborCost = (c.labor_requirement || 0) * (c.labor_cost_per_hour || 20);
    const fertCost = (c.fertilizer_requirement || 0) * (c.fertilizer_cost_per_kg || 1.5);
    const profit = rev - c.production_cost - laborCost - fertCost;

    const cropDisp = getCropDisplayName(c.name);

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${escapeHtml(cropDisp)}</strong></td>
      <td>${c.expected_yield}</td>
      <td>${c.price.toLocaleString()} ${curr}</td>
      <td>${c.production_cost.toLocaleString()} ${curr}</td>
      <td>${c.water_requirement.toLocaleString()}</td>
      <td>${c.labor_requirement || 0}</td>
      <td>${c.fertilizer_requirement || 0}</td>
      <td style="font-weight:800; color:${profit >= 0 ? '#34d399' : '#f87171'}">${profit.toLocaleString('en-US', {maximumFractionDigits:0})} ${curr}</td>
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
  const badge = document.getElementById("total-land-badge");
  if (badge) {
    const label = state.lang === "ar" ? `إجمالي الأرض: ${total.toFixed(1)} هكتار / فدان` : `Total Land: ${total.toFixed(1)} ha`;
    badge.textContent = label;
  }
}

function renderResults(res) {
  const curr = getCurrencySymbol();

  // KPI Cards
  document.getElementById("kpi-profit").textContent = `${res.expected_profit.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})} ${curr}`;
  document.getElementById("kpi-revenue").textContent = `${res.total_expected_revenue.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})} ${curr}`;
  
  const totalExpenses = res.total_production_cost + res.total_labor_cost + res.total_fertilizer_cost;
  document.getElementById("kpi-expenses").textContent = `${totalExpenses.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})} ${curr}`;
  
  const prodStr = state.lang === "ar" ? "زراعة" : "Prod";
  const laborStr = state.lang === "ar" ? "عمالة" : "Labor";
  const fertStr = state.lang === "ar" ? "أسمدة" : "Fert";
  document.getElementById("kpi-expenses-sub").textContent = `${prodStr}: ${res.total_production_cost.toFixed(0)} ${curr} | ${laborStr}: ${res.total_labor_cost.toFixed(0)} ${curr} | ${fertStr}: ${res.total_fertilizer_cost.toFixed(0)} ${curr}`;
  
  const statusStr = res.is_feasible ? (state.lang === "ar" ? "حل أمثل ممتاز" : "Feasible Optimal") : (state.lang === "ar" ? "غير قابل للحل" : "Infeasible");
  document.getElementById("kpi-status").textContent = statusStr;
  document.getElementById("kpi-solver-name").textContent = `${state.lang === "ar" ? "المحرك" : "Engine"}: ${res.version}`;

  renderResourceMeters(res);
  renderSuitabilityMatrix(res);
  renderRotationMatrix(res);
  renderFieldAllocations(res);
  renderBindingConstraints(res.binding_constraints);
}

function renderResourceMeters(res) {
  const container = document.getElementById("resource-meters-container");
  if (!container) return;
  container.innerHTML = "";

  const haUnit = state.lang === "ar" ? "هكتار/فدان" : "ha";
  const hrsUnit = state.lang === "ar" ? "ساعة" : "hours";
  const kgUnit = state.lang === "ar" ? "كجم" : "kg";

  const resources = [
    { name: state.lang === "ar" ? "مساحة الأرض" : "Land Area", used: res.total_land_used, limit: res.field_area_limit, unit: haUnit },
    { name: state.lang === "ar" ? "ميزانية المياه" : "Water Budget", used: res.total_water_used, limit: res.water_budget_limit, unit: "m³" },
    { name: state.lang === "ar" ? "ساعات العمالة" : "Labor Budget", used: res.total_labor_used, limit: res.labor_budget_limit, unit: hrsUnit },
    { name: state.lang === "ar" ? "كمية السماد" : "Fertilizer Budget", used: res.total_fertilizer_used, limit: res.fertilizer_budget_limit, unit: kgUnit },
  ];

  resources.forEach((r) => {
    if (r.limit === null || r.limit === undefined || r.limit === Infinity) return;

    const pct = Math.min(100, (r.used / r.limit) * 100);
    let barClass = "";
    if (pct >= 99.5) barClass = "danger";
    else if (pct >= 85) barClass = "warning";

    const usedLabel = state.lang === "ar" ? "المستهلك" : "Used";
    const capLabel = state.lang === "ar" ? "السعة القصوى" : "Capacity";

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
        <span>${usedLabel}: ${r.used.toLocaleString()} ${r.unit}</span>
        <span>${capLabel}: ${r.limit.toLocaleString()} ${r.unit}</span>
      </div>
    `;
    container.appendChild(box);
  });
}

function renderSuitabilityMatrix(res) {
  const card = document.getElementById("suitability-card");
  const table = document.getElementById("matrix-table");
  
  if (!res.suitability_details || res.suitability_details.length === 0) {
    if (card) card.style.display = "none";
    return;
  }
  if (card) card.style.display = "block";

  const fields = state.fields.map(f => f.name);
  const crops = state.crops.map(c => c.name);

  const matrix = {};
  res.suitability_details.forEach((item) => {
    matrix[`${item.field}__${item.crop}`] = item;
  });

  const headerLabel = state.lang === "ar" ? "الأرض \\ المحصول" : "Field \\ Crop";
  const okText = state.lang === "ar" ? "✅ مناسب" : "✅ Suitable";
  const noText = state.lang === "ar" ? "❌ غير مناسب" : "❌ Unsuitable";

  let html = `<thead><tr><th>${headerLabel}</th>`;
  crops.forEach(c => html += `<th>${escapeHtml(getCropDisplayName(c))}</th>`);
  html += "</tr></thead><tbody>";

  fields.forEach(f => {
    html += `<tr><th>${escapeHtml(f)}</th>`;
    crops.forEach(c => {
      const item = matrix[`${f}__${c}`];
      if (item) {
        if (item.suitable) {
          html += `<td class="matrix-cell-suitable" title="Suitable for planting">${okText}</td>`;
        } else {
          html += `<td class="matrix-cell-unsuitable" title="${escapeHtml(item.reason)}">${noText}<br><span style="font-size:0.7rem; opacity:0.8">${escapeHtml(item.reason)}</span></td>`;
        }
      } else {
        html += `<td>-</td>`;
      }
    });
    html += "</tr>";
  });
  html += "</tbody>";

  if (table) table.innerHTML = html;
}

function renderRotationMatrix(res) {
  const card = document.getElementById("rotation-card");
  const table = document.getElementById("rotation-matrix-table");

  if (!res.rotation_details || res.rotation_details.length === 0) {
    if (card) card.style.display = "none";
    return;
  }
  if (card) card.style.display = "block";

  const fields = state.fields.map(f => f.name);
  const crops = state.crops.map(c => c.name);

  const matrix = {};
  res.rotation_details.forEach((item) => {
    matrix[`${item.field}__${item.crop}`] = item;
  });

  const headerLabel = state.lang === "ar" ? "الأرض (المحصول السابق) \\ المحصول" : "Field (Prev Crop) \\ Crop";
  const okText = state.lang === "ar" ? "✅ تتابع ممتازة" : "✅ Suitable";
  const noText = state.lang === "ar" ? "❌ غير مسموح بالدورة" : "❌ Disallowed";

  let html = `<thead><tr><th>${headerLabel}</th>`;
  crops.forEach(c => html += `<th>${escapeHtml(getCropDisplayName(c))}</th>`);
  html += "</tr></thead><tbody>";

  fields.forEach(f => {
    const fObj = state.fields.find(item => item.name === f);
    const prevRaw = fObj && fObj.previous_crop ? fObj.previous_crop : "None";
    const prevDisp = getCropDisplayName(prevRaw);
    const prevPrefix = state.lang === "ar" ? "السابق: " : "Prev: ";

    html += `<tr><th>${escapeHtml(f)}<br><span style="font-size:0.75rem; color:var(--text-muted)">${prevPrefix}${escapeHtml(prevDisp)}</span></th>`;
    crops.forEach(c => {
      const item = matrix[`${f}__${c}`];
      if (item) {
        if (item.suitable) {
          html += `<td class="matrix-cell-suitable" title="${escapeHtml(item.reason)}">${okText}</td>`;
        } else {
          html += `<td class="matrix-cell-unsuitable" title="${escapeHtml(item.reason)}">${noText}<br><span style="font-size:0.7rem; opacity:0.8">${escapeHtml(item.reason)}</span></td>`;
        }
      } else {
        html += `<td>-</td>`;
      }
    });
    html += "</tr>";
  });
  html += "</tbody>";

  if (table) table.innerHTML = html;
}

function renderFieldAllocations(res) {
  const container = document.getElementById("field-allocations-container");
  if (!container) return;
  container.innerHTML = "";

  if (!res.field_allocations) return;

  const curr = getCurrencySymbol();
  const haUnit = state.lang === "ar" ? "هكتار/فدان" : "ha";
  const usedLabel = state.lang === "ar" ? "المستغل" : "Used";
  const noCropLabel = state.lang === "ar" ? "* لم تُخصص هذه الأرض لأي محصول." : "* No crops allocated to this field.";

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
        const cropDisp = getCropDisplayName(crop_name);

        itemsHtml += `
          <div class="crop-alloc-item">
            <span>🌾 <strong>${escapeHtml(cropDisp)}</strong></span>
            <span>${ha.toFixed(2)} ${haUnit} &nbsp; (<span style="color:#34d399">+${profitContrib.toLocaleString('en-US', {maximumFractionDigits:0})} ${curr}</span>)</span>
          </div>
        `;
      }
    });

    if (!itemsHtml) {
      itemsHtml = `<div class="crop-alloc-item" style="color:var(--text-dim)">${noCropLabel}</div>`;
    }

    const fieldLimit = res.field_land_limits ? res.field_land_limits[field_name] : (state.fields.find(f => f.name === field_name)?.area || 0);

    card.innerHTML = `
      <div class="field-alloc-header">
        <span>📍 ${escapeHtml(field_name)}</span>
        <span style="color:var(--text-muted)">${usedLabel}: ${usedHa.toFixed(1)} / ${fieldLimit.toFixed(1)} ${haUnit}</span>
      </div>
      ${itemsHtml}
    `;

    container.appendChild(card);
  });
}

function renderBindingConstraints(constraints) {
  const container = document.getElementById("binding-constraints-container");
  if (!container) return;
  container.innerHTML = "";

  if (!constraints) return;

  const usageLabel = state.lang === "ar" ? "الاستهلاك" : "Usage";

  constraints.forEach((c) => {
    const isBinding = c.is_binding;
    const tagText = isBinding ? (state.lang === "ar" ? "⚠️ ممر خانق (قيد منتهي)" : "⚠️ Bottleneck Constraint") : (state.lang === "ar" ? "✅ كافٍ ومتاح" : "✅ Sufficient");

    const item = document.createElement("div");
    item.className = `binding-item ${isBinding ? 'is-binding' : ''}`;
    item.innerHTML = `
      <div>
        <strong>${escapeHtml(c.resource)}</strong>
        <div style="font-size:0.8rem; color:var(--text-muted)">${usageLabel}: ${c.used.toLocaleString()} / ${c.limit ? c.limit.toLocaleString() : '∞'} ${c.unit} (${c.utilization_pct}%)</div>
      </div>
      <span class="binding-tag ${isBinding ? 'tag-binding' : 'tag-ok'}">
        ${tagText}
      </span>
    `;
    container.appendChild(item);
  });
}

// --- Field CRUD Modals ---

function openFieldModal(idx = null) {
  const modal = document.getElementById("field-modal");
  document.getElementById("field-edit-idx").value = idx !== null ? idx : "";

  let prevCrop = "";
  if (idx !== null) {
    const f = state.fields[idx];
    document.getElementById("field-modal-title").textContent = state.lang === "ar" ? "تعديل بيانات الأرض" : "Edit Field";
    document.getElementById("m-field-name").value = f.name;
    document.getElementById("m-field-area").value = f.area;
    document.getElementById("m-field-ph").value = f.ph;
    document.getElementById("m-field-ec").value = f.ec;
    document.getElementById("m-field-texture").value = f.texture;
    document.getElementById("m-field-om").value = f.organic_matter;
    prevCrop = f.previous_crop || "";
  } else {
    document.getElementById("field-modal-title").textContent = state.lang === "ar" ? "إضافة أرض جديدة" : "Add New Field";
    document.getElementById("m-field-name").value = `Field_${state.fields.length + 1}`;
    document.getElementById("m-field-area").value = 30.0;
    document.getElementById("m-field-ph").value = 6.8;
    document.getElementById("m-field-ec").value = 1.0;
    document.getElementById("m-field-texture").value = "Loam";
    document.getElementById("m-field-om").value = 2.0;
  }

  populatePreviousCropDropdown(prevCrop);
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
  const prevCropVal = document.getElementById("m-field-prev-crop").value.trim();
  const previous_crop = prevCropVal ? prevCropVal : null;

  if (!name || area <= 0) {
    alert(state.lang === "ar" ? "يرجى كتابة اسم أرض صحيح ومساحة أكبر من صفر." : "Please provide a valid field name and positive area.");
    return;
  }

  const fieldData = { name, area, ph, ec, texture, organic_matter: om, previous_crop };

  if (idxStr !== "") {
    state.fields[parseInt(idxStr)] = fieldData;
  } else {
    state.fields.push(fieldData);
  }

  closeFieldModal();
  renderFieldsTable();
}

function deleteField(idx) {
  const msg = state.lang === "ar" ? `هل أنت تأكد من حذف قطعة الأرض '${state.fields[idx].name}'؟` : `Are you sure you want to delete field '${state.fields[idx].name}'?`;
  if (confirm(msg)) {
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
    document.getElementById("crop-modal-title").textContent = state.lang === "ar" ? "تعديل بيانات المحصول" : "Edit Crop";
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
    document.getElementById("crop-modal-title").textContent = state.lang === "ar" ? "إضافة محصول جديد" : "Add New Crop";
    document.getElementById("m-crop-name").value = `Crop_${state.crops.length + 1}`;
    document.getElementById("m-crop-yield").value = 5.0;
    document.getElementById("m-crop-price").value = 12000.0;
    document.getElementById("m-crop-cost").value = 20000.0;
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
    alert(state.lang === "ar" ? "يرجى إدخال اسم المحصول، الإنتاجية، وسعر السوق بالجنيه بشكل صحيح." : "Please enter a valid crop name, yield, and market price in EGP.");
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
  const msg = state.lang === "ar" ? `هل أنت تأكد من حذف المحصول '${state.crops[idx].name}'؟` : `Are you sure you want to delete crop '${state.crops[idx].name}'?`;
  if (confirm(msg)) {
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
