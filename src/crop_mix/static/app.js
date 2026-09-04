// Crop Mix Planner Frontend Application Logic - Clean Farmer Edition (Bilingual & EGP)

// Application State
const state = {
  lang: "ar", // Default language: Arabic
  water_budget: 400000,
  labor_budget: 2500,
  fertilizer_budget: 15000,
  zone: "Delta",
  season: "Winter",
  fields: [],
  crops: [],
  ecocropSpecies: [],
  rotationCrops: [],
  lastResult: null,
};

// Bilingual Translation Dictionary (Clean, Natural Arabic & English)
const i18nData = {
  ar: {
    "landing.brandSub": "المنظومة الذكية للتخطيط الزراعي والدورة الزراعية",
    "nav.goOptimizer": "إدخال بيانات المزرعة 🚀",
    "landing.heroTag": "مصمم للمزارع المصري",
    "landing.heroTitle": "احسب أرباح مزرعتك وخطط لدورتك الزراعية الذكية",
    "landing.heroSub": "برنامج ذكي يحدد أفضل توزيع للمحاصيل على أراضيك لزيادة الربح الصافي، وترشيد مياه الري والسماد، وتطبيق قواعد الدورة الزراعية الرسمية.",
    "landing.startBtn": "ابدأ تخطيط مزرعتك الآن",
    "landing.learnMore": "تعرّف على المميزات",
    "features.title": "مميزات برنامج CropMix",
    "features.sub": "أدوات متكاملة تناسب الفلاح للوصول لأعلى إنتاجية وأفضل عائد مالي",
    "features.f1Title": "قواعد الدورة الزراعية",
    "features.f1Desc": "يفحص تتابع المحاصيل تلقائياً لمنع الإجهاد والأمراض (مثل تجنب الطماطم بعد البطاطس) وفق الجدول الموصى به.",
    "features.f2Title": "ترشيد المياه والميزانية",
    "features.f2Desc": "يحسب التكاليف والأرباح بدقة ويوزع الزراعة على حسب حصة المياه المتاحة لتحقيق أقصى عائد صافٍ.",
    "features.f3Title": "ملائمة نوع التربة",
    "features.f3Desc": "يطابق حموضة التربة، الملوحة، ونوع الأرض (طينية، رملية، صفراء) لضمان اختيار المحصول الأنسب لكل قطعة أرض.",
    "footer.text": "برنامج مخطط المحاصيل والدورة الزراعية • CropMix Business Planner",
    "nav.home": "الرئيسية",
    "opt.headerTagline": "إعداد بيانات المزرعة والأراضي",
    "opt.engineLabel": "المحرك:",
    "opt.loadPreset": "تحميل مزرعة افتراضية",
    "opt.generatePlanBtn": "حساب الخطة الحالية 🚀",
    "step1.title": "الميزانية العامة للمزرعة",
    "step1.sub": "المياه المتاحة والعمالة والأسمدة",
    "step1.waterLabel": "ميزانية المياه",
    "step1.laborLabel": "ساعات العمل",
    "step1.fertLabel": "كمية السماد",
    "step1.zoneLabel": "المنطقة في مصر",
    "step1.seasonLabel": "الموسم الزراعي",
    "zone.delta": "الدلتا (Delta)",
    "zone.middle": "مصر الوسطى (Middle Egypt)",
    "zone.upper": "مصر العليا (Upper Egypt)",
    "zone.sinai": "سيناء والأراضي الصحراوية (Sinai / Reclaimed)",
    "season.winter": "شتوي (Winter)",
    "season.summer": "صيفي (Summer)",
    "season.nili": "نيلي (Nili)",
    "season.perennial": "معمر / طوال العام (Perennial)",
    "step2.title": "قطع الأراضي والمحصول السابق",
    "step2.sub": "حدد المساحة ونوع التربة والزرعة السابقة لكل أرض",
    "step2.addField": "+ إضافة أرض جديدة",
    "step3.title": "المحاصيل المتاحة والأسعار",
    "step3.sub": "الإنتاجية المتوقعة، سعر الطن، وتكلفة الزراعة",
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
    "th.netProfit": "الربح المتوقع (EGP)",
    "res.headerTagline": "التوزيع الموصى به للمواسم القادمة",
    "res.editInputsBtn": "تعديل البيانات ✏️",
    "res.printBtn": "طباعة الخطة 🖨️",
    "res.planMainTitle": "توصية الخطة الزراعية للموسم الحالي",
    "res.planMainSub": "خطة موزعة على أراضيك بناءً على خصائص التربة الحالية والدورة الزراعية وأعلى ربحية صافية",
    "res.nextSeasonSectionTitle": "التخطيط للمواسم القادمة (التخطيط التتابعي والدورة الزراعية)",
    "res.nextSeasonSectionSub": "قم بالتخطيط للمواسم القادمة موسم بموسم بناءً على المحاصيل الموصى بها في هذا الموسم ودورة زراعية مستمرة بدون افتراضات تربة مستقبلية.",
    "res.planNextSeason": "التخطيط للموسم القادم",
    "kpi.profit": "إجمالي الربح الصافي المتوقع",
    "kpi.profitSub": "صافي الربح التقديري",
    "kpi.revenue": "إجمالي الإيرادات المتوقعة",
    "kpi.revenueSub": "قيمة بيع المحاصيل الإجمالية",
    "kpi.expenses": "إجمالي التكاليف والمصروفات",
    "kpi.status": "حالة التخطيط",
    "res.resourceTitle": "استهلاك الموارد وميزانية المزرعة",
    "res.rotationTitle": "مصفوفة الدورة الزراعية لكل أرض (V4)",
    "res.soilTitle": "مصفوفة ملائمة التربة لكل أرض",
    "res.allocTitle": "الخطة الزراعية الموصى بها لكل أرض",
    "res.allocSub": "تحديد المحصول والمساحة المخصصة لكل قطعة أرض لضمان أعلى عائد وتتابع زراعي ممتاز",
    "res.bindingTitle": "محلل القيود المحددة للربح",
    "res.detailsAccordion": "عرض التفاصيل الفنية الهندسية ومصفوفات التتابع",
    "modal.fieldName": "اسم قطعة الأرض",
    "modal.fieldArea": "المساحة (هكتار / فدان)",
    "modal.ph": "حموضة التربة (pH)",
    "modal.ec": "ملوحة التربة (EC dS/m)",
    "modal.texture": "نوع التربة",
    "modal.om": "المادة العضوية %",
    "modal.prevCrop": "المحصول السابق (سجل الدورة الزراعية V4)",
    "modal.ecocropAuto": "🌱 استيراد متطلبات التربة والمياه من موسوعة فاو إيكوكروب",
    "modal.cropName": "اسم المحصول",
    "modal.yield": "الإنتاجية المتوقعة (طن/هكتار)",
    "modal.price": "سعر بيع الطن (EGP/ton)",
    "modal.cost": "تكلفة الزراعة (EGP/ha)",
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
    "nav.goOptimizer": "Input Farm Data 🚀",
    "landing.heroTag": "Tailored for Egyptian Farmers",
    "landing.heroTitle": "Maximize Your Farm Profits & Plan Ideal Crop Rotations",
    "landing.heroSub": "Smart optimization tool that allocates crops to fields to maximize net profit, optimizes water and fertilizer, and enforces official rotation rules.",
    "landing.startBtn": "Start Farm Planning Now",
    "landing.learnMore": "Learn More Features",
    "features.title": "Why Farmers Trust CropMix?",
    "features.sub": "Integrated tools designed for agriculture to maximize yields and financial returns.",
    "features.f1Title": "Crop Rotation Rules",
    "features.f1Desc": "Automatically evaluates crop successions to prevent pests and soil degradation.",
    "features.f2Title": "Water & Profit Optimization",
    "features.f2Desc": "Calculates production costs and optimizes land use within water availability limits.",
    "features.f3Title": "Soil Chemistry Compatibility",
    "features.f3Desc": "Matches pH, EC salinity, and soil texture (Clay, Loam, Sandy) to ensure each crop fits the soil.",
    "footer.text": "Agricultural Crop & Rotation Planner • CropMix Business Planner",
    "nav.home": "Home",
    "opt.headerTagline": "Configure Farm & Field Data",
    "opt.engineLabel": "Engine:",
    "opt.loadPreset": "Load Default Farm",
    "opt.generatePlanBtn": "Generate Farm Allocation Plan 🚀",
    "step1.title": "Global Farm Budgets",
    "step1.sub": "Set water, labor, and fertilizer availability",
    "step1.waterLabel": "Water Budget",
    "step1.laborLabel": "Labor Hours",
    "step1.fertLabel": "Fertilizer Budget",
    "step1.zoneLabel": "Region in Egypt",
    "step1.seasonLabel": "Agricultural Season",
    "zone.delta": "Delta",
    "zone.middle": "Middle Egypt",
    "zone.upper": "Upper Egypt",
    "zone.sinai": "Sinai & Reclaimed Lands",
    "season.winter": "Winter",
    "season.summer": "Summer",
    "season.nili": "Nili",
    "season.perennial": "Perennial",
    "step2.title": "Farm Fields & Rotation History",
    "step2.sub": "Manage field boundaries, soil chemistry, and previous crop",
    "step2.addField": "+ Add New Field",
    "step3.title": "Crop Catalog & Prices",
    "step3.sub": "Configure expected yield, market price, and costs per hectare",
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
    "res.headerTagline": "Recommended Seasonal Plan",
    "res.editInputsBtn": "Edit Data ✏️",
    "res.printBtn": "Print Plan 🖨️",
    "res.planMainTitle": "Current Season Farm Allocation Plan",
    "res.planMainSub": "Optimal allocation across fields based on current measured soil conditions, rotation rules, and profit",
    "res.nextSeasonSectionTitle": "Future Multi-Season Planning (Sequential Crop Rotation)",
    "res.nextSeasonSectionSub": "Plan future seasons one by one based on the recommended crop allocations of the current season without future soil assumptions.",
    "res.planNextSeason": "Plan Next Season",
    "kpi.profit": "Expected Net Profit",
    "kpi.profitSub": "Estimated Net Profit",
    "kpi.revenue": "Expected Gross Revenue",
    "kpi.revenueSub": "Total crop sales value",
    "kpi.expenses": "Total Expenses & Costs",
    "kpi.status": "Planner Status",
    "res.resourceTitle": "Resource & Budget Utilization",
    "res.rotationTitle": "Crop Rotation Matrix (V4)",
    "res.soilTitle": "Soil Suitability Matrix",
    "res.allocTitle": "Recommended Allocation Plan by Field",
    "res.allocSub": "Specific crops and hectares assigned to each field for maximum returns",
    "res.bindingTitle": "Bottleneck Constraints Analyzer",
    "res.detailsAccordion": "Technical Inspection & Rotation Details",
    "modal.fieldName": "Field Name",
    "modal.fieldArea": "Area (hectares/feddans)",
    "modal.ph": "Soil pH",
    "modal.ec": "Salinity EC (dS/m)",
    "modal.texture": "Soil Texture",
    "modal.om": "Organic Matter %",
    "modal.prevCrop": "Previous Crop (V4 History)",
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
  document.querySelectorAll(".lang-text-btn").forEach((btn) => {
    btn.textContent = langToggleText;
  });

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

// Canonical crop name lookup for cross-language resolution
const canonicalCropMap = {
  "wheat": "Wheat",
  "قمح": "Wheat",
  "yellow corn": "Yellow Corn",
  "corn": "Yellow Corn",
  "maize": "Yellow Corn",
  "ذرة صفراء": "Yellow Corn",
  "soybean": "Soybean",
  "soybeans": "Soybean",
  "فول صويا": "Soybean",
  "tomato": "Tomato",
  "tomatoes": "Tomato",
  "طماطم": "Tomato",
  "cotton": "Cotton",
  "قطن": "Cotton",
  "potato": "Potato",
  "potatoes": "Potato",
  "بطاطس": "Potato",
  "onion": "Onion",
  "onions": "Onion",
  "بصل": "Onion",
  "barley": "Barley",
  "شعير": "Barley",
  "rice": "Rice",
  "أرز": "Rice",
  "sugar beet": "Sugar Beet",
  "sugarbeet": "Sugar Beet",
  "بنجر السكر": "Sugar Beet",
  "sugar cane": "Sugar Cane",
  "sugarcane": "Sugar Cane",
  "قصب السكر": "Sugar Cane",
  "alfalfa": "Alfalfa",
  "berseem": "Alfalfa",
  "برسيم": "Alfalfa",
  "برسيم حجازي": "Alfalfa",
};

function getCanonicalCropName(cropName) {
  if (!cropName) return "";
  const clean = String(cropName).trim().toLowerCase();
  return canonicalCropMap[clean] || String(cropName).trim();
}

function getCurrencySymbol() {
  return state.lang === "ar" ? "ج.م" : "EGP";
}

function getCropDisplayName(c) {
  let name = "";
  let nameAr = "";
  if (typeof c === "object" && c !== null) {
    name = c.name || "";
    nameAr = c.name_arabic || c.arabic_name || "";
  } else {
    name = String(c || "");
  }

  const canonical = getCanonicalCropName(name);

  if (state.lang === "ar") {
    if (cropNamesAr[canonical]) return cropNamesAr[canonical];
    if (cropNamesAr[name]) return cropNamesAr[name];
    if (nameAr) return `${nameAr} (${canonical || name})`;
  }
  return canonical || name;
}

function initEventListeners() {
  document.getElementById("btn-load-preset").addEventListener("click", loadPresetData);
  document.getElementById("btn-run-optimize").addEventListener("click", runOptimizationAndShowPlan);
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

  const zoneElem = document.getElementById("farm-zone");
  if (zoneElem) {
    zoneElem.addEventListener("change", (e) => {
      state.zone = e.target.value;
      updateCropsWaterRequirements();
    });
  }

  const seasonElem = document.getElementById("farm-season");
  if (seasonElem) {
    seasonElem.addEventListener("change", (e) => {
      state.season = e.target.value;
      updateCropsWaterRequirements();
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

async function updateCropsWaterRequirements() {
  for (let c of state.crops) {
    try {
      const res = await fetch(`/api/water/lookup/${encodeURIComponent(c.name)}?zone=${encodeURIComponent(state.zone)}&season=${encodeURIComponent(state.season)}`);
      if (res.ok) {
        const data = await res.json();
        if (data.water_requirement && data.water_requirement > 0) {
          c.water_requirement = data.water_requirement;
        }
      }
    } catch (err) {
      console.error(`Failed to update water requirement for ${c.name}:`, err);
    }
  }
  renderCropsTable();
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
  } catch (err) {
    console.error(err);
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

  const defaultMsg = state.lang === "ar" ? "اختر المحصول من قائمة فاو..." : "Select FAO EcoCrop Species...";
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

    let waterReq = item.water_requirement || 4000.0;
    try {
      const wRes = await fetch(`/api/water/lookup/${encodeURIComponent(item.name)}?zone=${encodeURIComponent(state.zone)}&season=${encodeURIComponent(state.season)}`);
      if (wRes.ok) {
        const wData = await wRes.json();
        if (wData.water_requirement && wData.water_requirement > 0) {
          waterReq = wData.water_requirement;
        }
      }
    } catch (e) {
      console.error("Water lookup error:", e);
    }

    const existingIdx = state.crops.findIndex(c => c.name.toLowerCase() === item.name.toLowerCase());
    const cropData = {
      name: item.name,
      expected_yield: item.default_expected_yield || 5.0,
      price: item.default_price || 12000.0,
      production_cost: item.default_production_cost || 20000.0,
      water_requirement: waterReq,
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

    let waterReq = item.water_requirement || 4000.0;
    try {
      const wRes = await fetch(`/api/water/lookup/${encodeURIComponent(item.name)}?zone=${encodeURIComponent(state.zone)}&season=${encodeURIComponent(state.season)}`);
      if (wRes.ok) {
        const wData = await wRes.json();
        if (wData.water_requirement && wData.water_requirement > 0) {
          waterReq = wData.water_requirement;
        }
      }
    } catch (e) {}

    document.getElementById("m-crop-name").value = item.name;
    document.getElementById("m-crop-yield").value = item.default_expected_yield || 5.0;
    document.getElementById("m-crop-price").value = item.default_price || 12000.0;
    document.getElementById("m-crop-cost").value = item.default_production_cost || 20000.0;
    document.getElementById("m-crop-water").value = waterReq;
    document.getElementById("m-crop-min-ph").value = item.min_ph;
    document.getElementById("m-crop-max-ph").value = item.max_ph;
    document.getElementById("m-crop-max-ec").value = item.max_ec;
    document.getElementById("m-crop-textures").value = item.suitable_textures ? item.suitable_textures.join(", ") : "Loam, Clay, Silt";
  } catch (err) {
    console.error("Error auto-filling from EcoCrop:", err);
  }
}

async function runOptimizationAndShowPlan() {
  const version = document.getElementById("optimizer-version").value;
  const statusPill = document.getElementById("status-pill");
  
  statusPill.textContent = state.lang === "ar" ? "جاري التخطيط..." : "Calculating Plan...";
  statusPill.className = "status-pill";

  const payload = {
    version: version,
    zone: state.zone,
    season: state.season,
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

    statusPill.textContent = state.lang === "ar" ? "تم حساب الخطة بنجاح" : `Plan Solved (${result.status})`;
    statusPill.className = "status-pill success";

    // Switch to View 3 (Results Page)
    navigateTo("optimizer-results");
  } catch (err) {
    console.error(err);
    alert((state.lang === "ar" ? "خطأ في حساب الخطة: " : "Plan Error: ") + err.message);
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
      <td><span class="badge badge-secondary">${escapeHtml(prevCrop)}</span></td>
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
    const yieldVal = Number(c.expected_yield) || 0;
    const priceVal = Number(c.price) || 0;
    const costVal = Number(c.production_cost) || 0;
    const waterVal = Number(c.water_requirement) || 0;
    const laborVal = Number(c.labor_requirement) || 0;
    const laborRateVal = Number(c.labor_cost_per_hour) || 20;
    const fertVal = Number(c.fertilizer_requirement) || 0;
    const fertRateVal = Number(c.fertilizer_cost_per_kg) || 1.5;

    const rev = yieldVal * priceVal;
    const laborCost = laborVal * laborRateVal;
    const fertCost = fertVal * fertRateVal;
    const profit = rev - costVal - laborCost - fertCost;
    const cropDisp = getCropDisplayName(c);

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${escapeHtml(cropDisp)}</strong></td>
      <td>${yieldVal}</td>
      <td>${priceVal.toLocaleString()} ${curr}</td>
      <td>${costVal.toLocaleString()} ${curr}</td>
      <td>${waterVal.toLocaleString()}</td>
      <td>${laborVal}</td>
      <td>${fertVal}</td>
      <td style="font-weight:800; color:${profit >= 0 ? '#059669' : '#dc2626'}">${profit.toLocaleString('en-US', {maximumFractionDigits:0})} ${curr}</td>
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
  document.getElementById("kpi-profit").textContent = `${res.expected_profit.toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 0})} ${curr}`;
  document.getElementById("kpi-revenue").textContent = `${res.total_expected_revenue.toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 0})} ${curr}`;
  
  const totalExpenses = res.total_production_cost + res.total_labor_cost + res.total_fertilizer_cost;
  document.getElementById("kpi-expenses").textContent = `${totalExpenses.toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 0})} ${curr}`;
  
  const statusStr = res.is_feasible ? (state.lang === "ar" ? "خطة ممتازة ومثالية" : "Optimal Plan") : (state.lang === "ar" ? "غير قابل للحل" : "Infeasible");
  document.getElementById("kpi-status").textContent = statusStr;

  renderSeasonalFieldPlanCards(res);
  renderMainFinancialProjection(res.financial_projection);
  renderResourceMeters(res);
  renderSuitabilityMatrix(res);
  renderRotationMatrix(res);
  renderBindingConstraints(res.binding_constraints);
}

// Render Part 1 Financial Projection Section on Main Recommendation Page
function renderMainFinancialProjection(finData) {
  const card = document.getElementById("financial-projection-card");
  const kpiGrid = document.getElementById("main-financial-kpi-grid");
  const tbody = document.getElementById("main-financial-tbody");

  if (!finData || !finData.farm_summary) {
    if (card) card.style.display = "none";
    return;
  }
  if (card) card.style.display = "block";

  const curr = getCurrencySymbol();
  const haUnit = state.lang === "ar" ? "هكتار/فدان" : "ha";
  const s = finData.farm_summary;

  if (kpiGrid) {
    kpiGrid.innerHTML = `
      <div style="background:var(--bg-subtle); padding:12px; border-radius:10px; border:1px solid var(--border-color); text-align:center;">
        <span style="font-size:0.8rem; color:var(--text-muted); display:block;">${state.lang === 'ar' ? 'إجمالي المساحة' : 'Total Area'}</span>
        <strong style="font-size:1.1rem; color:var(--primary-nile);">${s.total_area} ${haUnit}</strong>
      </div>
      <div style="background:var(--bg-subtle); padding:12px; border-radius:10px; border:1px solid var(--border-color); text-align:center;">
        <span style="font-size:0.8rem; color:var(--text-muted); display:block;">${state.lang === 'ar' ? 'إجمالي الإيرادات' : 'Gross Revenue'}</span>
        <strong style="font-size:1.1rem; color:var(--primary-green);">${s.total_expected_revenue.toLocaleString()} ${curr}</strong>
      </div>
      <div style="background:var(--bg-subtle); padding:12px; border-radius:10px; border:1px solid var(--border-color); text-align:center;">
        <span style="font-size:0.8rem; color:var(--text-muted); display:block;">${state.lang === 'ar' ? 'تكلفة الإنتاج' : 'Production Cost'}</span>
        <strong style="font-size:1.1rem; color:var(--danger-text);">${s.total_production_cost.toLocaleString()} ${curr}</strong>
      </div>
      <div style="background:var(--bg-subtle); padding:12px; border-radius:10px; border:1px solid var(--border-color); text-align:center;">
        <span style="font-size:0.8rem; color:var(--text-muted); display:block;">${state.lang === 'ar' ? 'تكلفة العمالة' : 'Labor Cost'}</span>
        <strong style="font-size:1.1rem; color:var(--danger-text);">${s.total_labor_cost.toLocaleString()} ${curr}</strong>
      </div>
      <div style="background:var(--bg-subtle); padding:12px; border-radius:10px; border:1px solid var(--border-color); text-align:center;">
        <span style="font-size:0.8rem; color:var(--text-muted); display:block;">${state.lang === 'ar' ? 'تكلفة الأسمدة' : 'Fertilizer Cost'}</span>
        <strong style="font-size:1.1rem; color:var(--danger-text);">${s.total_fertilizer_cost.toLocaleString()} ${curr}</strong>
      </div>
      <div style="background:var(--bg-subtle); padding:12px; border-radius:10px; border:1px solid var(--border-color); text-align:center;">
        <span style="font-size:0.8rem; color:var(--text-muted); display:block;">${state.lang === 'ar' ? 'إجمالي التكاليف' : 'Total Costs'}</span>
        <strong style="font-size:1.1rem; color:var(--danger-text);">${s.total_cost.toLocaleString()} ${curr}</strong>
      </div>
      <div style="background:var(--gold-bg); padding:12px; border-radius:10px; border:1px solid var(--gold-light); text-align:center;">
        <span style="font-size:0.8rem; color:var(--gold-accent); display:block; font-weight:700;">${state.lang === 'ar' ? 'صافي الربح المتوقع' : 'Net Profit'}</span>
        <strong style="font-size:1.2rem; color:var(--primary-nile); font-weight:800;">${s.total_expected_net_profit.toLocaleString()} ${curr}</strong>
      </div>
      <div style="background:var(--bg-subtle); padding:12px; border-radius:10px; border:1px solid var(--border-color); text-align:center;">
        <span style="font-size:0.8rem; color:var(--text-muted); display:block;">${state.lang === 'ar' ? 'هامش الربح' : 'Profit Margin'}</span>
        <strong style="font-size:1.1rem; color:var(--primary-green);">${s.overall_profit_margin_pct}%</strong>
      </div>
    `;
  }

  if (tbody && finData.field_projections) {
    tbody.innerHTML = "";
    Object.entries(finData.field_projections).forEach(([fName, cMap]) => {
      Object.entries(cMap).forEach(([cName, p]) => {
        if (p.allocated_area <= 0) return;
        const cropAr = getCropDisplayName(cName);
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${escapeHtml(fName)}</strong></td>
          <td><span class="badge badge-info">${escapeHtml(cropAr)}</span></td>
          <td>${p.allocated_area.toFixed(2)} ${haUnit}</td>
          <td style="color:var(--primary-green); font-weight:700;">${p.expected_revenue.toLocaleString()} ${curr}</td>
          <td>${p.production_cost.toLocaleString()} ${curr}</td>
          <td>${p.labor_cost.toLocaleString()} ${curr}</td>
          <td>${p.fertilizer_cost.toLocaleString()} ${curr}</td>
          <td style="color:var(--danger-text); font-weight:700;">${p.total_cost.toLocaleString()} ${curr}</td>
          <td style="color:var(--primary-nile); font-weight:800;">${p.net_profit.toLocaleString()} ${curr}</td>
          <td>${p.profit_per_hectare.toLocaleString()} ${curr}/${haUnit}</td>
          <td style="font-weight:700;">${p.profit_margin_pct}%</td>
        `;
        tbody.appendChild(tr);
      });
    });
  }
}

// Render Seasonal Allocation Plan Cards for Farmer
function renderSeasonalFieldPlanCards(res) {
  const container = document.getElementById("field-allocations-container");
  if (!container) return;
  container.innerHTML = "";

  if (!res.field_allocations) return;

  const curr = getCurrencySymbol();
  const haUnit = state.lang === "ar" ? "هكتار/فدان" : "ha";
  const prevLabel = state.lang === "ar" ? "المحصول السابق" : "Previous Crop";
  const allocTitle = state.lang === "ar" ? "المحصول الموصى بزراعته" : "Recommended Crop";
  const noCropLabel = state.lang === "ar" ? "أرض بور للموسم القادم" : "Fallow Field Next Season";

  Object.entries(res.field_allocations).forEach(([field_name, allocations]) => {
    const card = document.createElement("div");
    card.className = "field-plan-card";

    const fObj = state.fields.find(f => f.name === field_name);
    const fieldArea = fObj ? fObj.area : (res.field_land_limits ? res.field_land_limits[field_name] : 0);
    const prevRaw = fObj && fObj.previous_crop ? fObj.previous_crop : "None";
    const prevDisp = getCropDisplayName(prevRaw);

    let mainCropHtml = "";
    let allocatedSum = 0;

    Object.entries(allocations).forEach(([crop_name, ha]) => {
      if (ha > 0.001) {
        allocatedSum += ha;
        const cropObj = state.crops.find(c => c.name === crop_name);
        const profitPerHa = cropObj ? (cropObj.expected_yield * cropObj.price - cropObj.production_cost - (cropObj.labor_requirement||0)*(cropObj.labor_cost_per_hour||20) - (cropObj.fertilizer_requirement||0)*(cropObj.fertilizer_cost_per_kg||1.5)) : 0;
        const totalProfitContrib = ha * profitPerHa;
        const cropDisp = getCropDisplayName(crop_name);

        mainCropHtml += `
          <div class="field-crop-allocation-box">
            <div style="font-size:0.8rem; color:var(--text-muted); font-weight:700;">${allocTitle}</div>
            <div class="crop-alloc-name">🌾 ${escapeHtml(cropDisp)}</div>
            <div class="crop-alloc-ha">المساحة: ${ha.toFixed(1)} ${haUnit} (من أصل ${fieldArea.toFixed(1)})</div>
            <div class="crop-alloc-profit">+${totalProfitContrib.toLocaleString('en-US', {maximumFractionDigits:0})} ${curr} ربح متوقع</div>
          </div>
        `;
      }
    });

    if (!mainCropHtml) {
      mainCropHtml = `
        <div class="field-crop-allocation-box" style="background:var(--bg-main);">
          <div class="crop-alloc-name" style="color:var(--text-dim);">😴 ${noCropLabel}</div>
          <div style="font-size:0.85rem; color:var(--text-muted);">ترك الأرض بدون زراعة لترشيد المياه المتاحة للمزرعة</div>
        </div>
      `;
    }

    // Rotation & Soil Badges
    const rotationCheck = state.lang === "ar" ? "✅ تتابع ممتازة بالدورة الزراعية" : "✅ Recommended Rotation";
    const soilCheck = state.lang === "ar" ? "🌱 ملائمة لنوع التربة" : "🌱 Suitable Soil Chemistry";

    card.innerHTML = `
      <div class="field-plan-header">
        <span class="field-title-text">📍 ${escapeHtml(field_name)}</span>
        <span class="field-area-tag">${fieldArea.toFixed(1)} ${haUnit}</span>
      </div>
      <div class="field-prev-row">
        <span>${prevLabel}: <strong>${escapeHtml(prevDisp)}</strong></span>
      </div>
      ${mainCropHtml}
      <div class="field-badges-row">
        <span class="badge badge-info">${rotationCheck}</span>
        <span class="badge badge-secondary">${soilCheck}</span>
      </div>
    `;

    container.appendChild(card);
  });
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
    { name: state.lang === "ar" ? "ساعات العمالة" : "Labor Hours", used: res.total_labor_used, limit: res.labor_budget_limit, unit: hrsUnit },
    { name: state.lang === "ar" ? "كمية السماد" : "Fertilizer Budget", used: res.total_fertilizer_used, limit: res.fertilizer_budget_limit, unit: kgUnit },
  ];

  resources.forEach((r) => {
    if (r.limit === null || r.limit === undefined || r.limit === Infinity) return;

    const pct = Math.min(100, (r.used / r.limit) * 100);
    let barClass = "";
    if (pct >= 99.5) barClass = "danger";
    else if (pct >= 85) barClass = "warning";

    const usedLabel = state.lang === "ar" ? "المستهلك" : "Used";
    const capLabel = state.lang === "ar" ? "المتاح" : "Capacity";

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
          html += `<td class="matrix-cell-suitable">${okText}</td>`;
        } else {
          html += `<td class="matrix-cell-unsuitable" title="${escapeHtml(item.reason)}">${noText}</td>`;
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
  const okText = state.lang === "ar" ? "✅ مسموح" : "✅ Suitable";
  const noText = state.lang === "ar" ? "❌ غير مسموح" : "❌ Disallowed";

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
          html += `<td class="matrix-cell-unsuitable" title="${escapeHtml(item.reason)}">${noText}</td>`;
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

function renderBindingConstraints(constraints) {
  const container = document.getElementById("binding-constraints-container");
  if (!container) return;
  container.innerHTML = "";

  if (!constraints) return;

  const usageLabel = state.lang === "ar" ? "الاستهلاك" : "Usage";

  constraints.forEach((c) => {
    const isBinding = c.is_binding;
    const tagText = isBinding ? (state.lang === "ar" ? "⚠️ قيد منتهي بالكامل" : "⚠️ Bottleneck") : (state.lang === "ar" ? "✅ كافٍ ومتاح" : "✅ Sufficient");

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
    alert(state.lang === "ar" ? "يرجى إدخال اسم المحصول، الإنتاجية، وسعر السوق بشكل صحيح." : "Please enter a valid crop name, yield, and market price.");
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


// ==========================================================================
// INTERNSHIP 4B PHASE 2: MULTI-SEASON CROP ROTATION PLANNER UI LOGIC
// ==========================================================================

let multiSeasonState = {
  sessionId: "ms_session_" + Date.now(),
  candidateCrops: [],
  currentPreviousCrops: {},
  waterBudget: 400000,
  laborBudget: 2500,
  fertilizerBudget: 15000,
  currentSeasonName: "Summer",
  currentPlan: null,
  step: 1, // 1: Candidate Selection, 2: Season Setup, 3: Season Results
};

function openMultiSeasonModal() {
  document.getElementById("multi-season-modal").classList.add("active");

  // Sync initial budgets from main state if not yet configured
  if (state.water_budget) multiSeasonState.waterBudget = state.water_budget;
  if (state.labor_budget) multiSeasonState.laborBudget = state.labor_budget;
  if (state.fertilizer_budget) multiSeasonState.fertilizerBudget = state.fertilizer_budget;

  if (multiSeasonState.step === 1 || multiSeasonState.candidateCrops.length === 0) {
    renderMultiSeasonStep1();
  } else if (multiSeasonState.step === 2) {
    renderMultiSeasonStep2();
  } else if (multiSeasonState.step === 3 && multiSeasonState.currentPlan) {
    renderMultiSeasonStep3();
  } else {
    renderMultiSeasonStep1();
  }
}

function closeMultiSeasonModal() {
  document.getElementById("multi-season-modal").classList.remove("active");
}

// STEP 1: Candidate Crop Selection (Selected ONCE at session start)
function renderMultiSeasonStep1() {
  multiSeasonState.step = 1;
  const modalTitle = document.getElementById("ms-modal-title");
  const modalBody = document.getElementById("ms-modal-body");

  modalTitle.innerHTML = `🌱 الخطوة 1: اختيار المحاصيل المرشحة (مرة واحدة)`;

  // Generate available crops checklist from state
  const availableCrops = state.crops.length > 0 ? state.crops : [
    { name: "Wheat" }, { name: "Yellow Corn" }, { name: "Soybean" }, { name: "Tomato" }, { name: "Cotton" }
  ];

  let cropsChecklistHtml = availableCrops.map((c) => {
    const isChecked = multiSeasonState.candidateCrops.length === 0 || multiSeasonState.candidateCrops.includes(c.name);
    const arName = c.name_arabic || c.name;
    const seasonsStr = (c.allowed_seasons || ["Winter", "Summer"]).join(", ");
    return `
      <label class="checkbox-card" style="display:flex; align-items:center; gap:10px; background:var(--bg-subtle); padding:12px; border-radius:10px; border:1px solid var(--border-color); cursor:pointer;">
        <input type="checkbox" class="ms-candidate-cb" value="${escapeHtml(c.name)}" ${isChecked ? 'checked' : ''} style="width:20px; height:20px; accent-color:var(--primary-green);">
        <div>
          <strong style="font-size:1.05rem; color:var(--primary-nile);">${escapeHtml(arName)} (${escapeHtml(c.name)})</strong>
          <div style="font-size:0.8rem; color:var(--text-muted);">المواسم المتاحة: ${escapeHtml(seasonsStr)}</div>
        </div>
      </label>
    `;
  }).join("");

  modalBody.innerHTML = `
    <div style="margin-bottom: 20px;">
      <p style="font-size:1rem; color:var(--text-muted); margin-bottom:15px;">
        اختر قائمة المحاصيل التي ترغب بتضمينها في التخطيط للمواسم القادمة. يتم تحديد هذه القائمة <strong>مرة واحدة</strong> وسيتم اعتمادها لكل المواسم التالية تلقائياً (ويمكنك تعديلها عند الحاجة).
      </p>
      
      <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap:12px; margin-bottom:24px;">
        ${cropsChecklistHtml}
      </div>

      <div style="display:flex; justify-content:flex-end; gap:12px; border-top:1px solid var(--border-color); padding-top:16px;">
        <button class="btn btn-secondary" onclick="closeMultiSeasonModal()">إلغاء</button>
        <button class="btn btn-primary" onclick="submitCandidateCrops()" style="background:var(--primary-green);">
          <span>بدء التخطيط للمواسم القادمة 🚀</span>
        </button>
      </div>
    </div>
  `;
}

function getFarmRequestPayload() {
  const version = document.getElementById("optimizer-version")
    ? document.getElementById("optimizer-version").value
    : "v4";
  return {
    version: version,
    zone: state.zone,
    season: state.season,
    water_budget: parseFloat(document.getElementById("budget-water") ? document.getElementById("budget-water").value : state.water_budget) || state.water_budget,
    labor_budget: parseFloat(document.getElementById("budget-labor") ? document.getElementById("budget-labor").value : state.labor_budget) || state.labor_budget,
    fertilizer_budget: parseFloat(document.getElementById("budget-fertilizer") ? document.getElementById("budget-fertilizer").value : state.fertilizer_budget) || state.fertilizer_budget,
    fields: state.fields.map(f => Object.assign({}, f)),
    crops: state.crops.map(c => Object.assign({}, c)),
  };
}

function submitCandidateCrops() {
  const checkboxes = document.querySelectorAll(".ms-candidate-cb:checked");
  const selectedCrops = Array.from(checkboxes).map(cb => cb.value);

  if (selectedCrops.length === 0) {
    alert("يرجى اختيار محصول واحد على الأقل للمتابعة.");
    return;
  }

  multiSeasonState.candidateCrops = selectedCrops;

  // Build farm request payload
  const farmRequest = getFarmRequestPayload();

  // Extract Season 1 recommendation per field
  const s1Rec = {};
  if (state.lastResult && state.lastResult.field_allocations) {
    for (const [fName, allocMap] of Object.entries(state.lastResult.field_allocations)) {
      let maxArea = 0;
      let topCrop = null;
      for (const [cName, ha] of Object.entries(allocMap)) {
        if (ha > maxArea) {
          maxArea = ha;
          topCrop = cName;
        }
      }
      if (topCrop) {
        s1Rec[fName] = topCrop;
      }
    }
  }

  // Initialize session via API without re-optimizing Season 1
  fetch("/api/multi-season/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: multiSeasonState.sessionId,
      candidate_crops: selectedCrops,
      season_1_recommendation: s1Rec,
      current_season_name: state.season,
      water_budget: farmRequest.water_budget,
      labor_budget: farmRequest.labor_budget,
      fertilizer_budget: farmRequest.fertilizer_budget,
      farm_request: farmRequest,
    }),
  })
    .then(res => res.json())
    .then(data => {
      if (data.detail) {
        alert("خطأ: " + data.detail);
        return;
      }
      multiSeasonState.currentPreviousCrops = data.current_previous_crops;
      multiSeasonState.waterBudget = data.current_water_budget;
      multiSeasonState.laborBudget = data.current_labor_budget;
      multiSeasonState.fertilizerBudget = data.current_fertilizer_budget;

      // Set currentSeasonName to the current optimizer season so getSeasonDropdownOptions()
      // correctly offers what comes AFTER it in the Egyptian 3-season cycle
      multiSeasonState.currentSeasonName = state.season;

      renderMultiSeasonStep2();
    })
    .catch(err => {
      console.error("Error starting multi-season session:", err);
      renderMultiSeasonStep2();
    });
}

// Returns dropdown options for the next season.
// Auto-cycle is strictly Winter ⇔ Summer.
// Nili is always shown as an optional 3rd choice but never auto-selected.
function getSeasonDropdownOptions(lastKnownSeason) {
  const nextAuto = (lastKnownSeason === "Winter") ? "Summer" : "Winter";
  const seasonAr = { Winter: "شتوي (Winter)", Summer: "صيفي (Summer)", Nili: "نيلي (Nili)" };
  return [
    { value: nextAuto, label: seasonAr[nextAuto] },  // always auto-selected
    { value: nextAuto === "Summer" ? "Winter" : "Summer", label: seasonAr[nextAuto === "Summer" ? "Winter" : "Summer"] },
    { value: "Nili",    label: seasonAr["Nili"] },   // always available, never auto-selected
  ];
}

// STEP 2: Season Planning & Budget Carry-Forward View
function renderMultiSeasonStep2() {
  multiSeasonState.step = 2;
  const modalTitle = document.getElementById("ms-modal-title");
  const modalBody = document.getElementById("ms-modal-body");

  const seasonNum = (multiSeasonState.seasonHistory ? multiSeasonState.seasonHistory.length : 0) + 2;
  modalTitle.innerHTML = `🗓️ الخطوة 2: تخطيط الموسم القادم (موسم ${seasonNum})`;

  // Previous crops list
  let prevCropsHtml = "";
  if (state.fields && state.fields.length > 0) {
    prevCropsHtml = state.fields.map(f => {
      const prevC = multiSeasonState.currentPreviousCrops[f.name] || f.previous_crop || "لا يوجد (أرض بور)";
      const arCrop = getCropDisplayName(prevC);
      return `
        <div style="background:var(--bg-card); padding:10px 14px; border-radius:8px; border:1px solid var(--border-color); display:flex; justify-content:space-between; align-items:center;">
          <div>
            <strong>📍 ${escapeHtml(f.name)}</strong>
            <span style="font-size:0.85rem; color:var(--text-muted);">(${f.area} هكتار)</span>
          </div>
          <div style="color:var(--primary-nile); font-weight:700;">
            المحصول السابق: <span style="color:var(--gold-accent);">${escapeHtml(arCrop)}</span>
          </div>
        </div>
      `;
    }).join("");
  }

  modalBody.innerHTML = `
    <div style="display:flex; flex-direction:column; gap:20px;">
      
      <!-- Explicit Future Soil Notice Banner (User Rule 3) -->
      <div style="background:#fffbeb; border:1px solid #fcd34d; padding:12px 16px; border-radius:10px; color:#92400e; font-weight:700; font-size:0.95rem; display:flex; align-items:center; gap:10px;">
        <span style="font-size:1.2rem;">⚠️</span>
        <span>المواسم المستقبلية: لا يتم استخدام خصائص التربة الحالية لعدم توفر قياسات مستقبلية.</span>
      </div>

      <div style="background:var(--bg-subtle); padding:16px; border-radius:12px; border:1px solid var(--border-color);">
        <h4 style="color:var(--primary-nile); margin-bottom:12px;">📅 الموسم القادم المحدد تلقائياً</h4>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px; align-items:start;">
          <div>
            <label style="display:block; font-weight:700; margin-bottom:6px;">اختر الموسم القادم:</label>
            <select id="ms-season-select" class="select-input" style="width:100%;">
              ${(() => { const opts = getSeasonDropdownOptions(multiSeasonState.currentSeasonName); return opts.map((o, i) => `<option value="${o.value}" ${i === 0 ? 'selected' : ''}>${o.label}</option>`).join(''); })()}
            </select>
            <p style="margin-top:6px; font-size:0.8rem; color:var(--text-muted);">&#x21BA; الدورة التلقائية: شتوي &#x2194; صيفي &nbsp;&bull;&nbsp; نيلي: اختياري</p>
          </div>
          <div style="background:var(--gold-bg); padding:10px 14px; border-radius:8px; border:1px solid var(--gold-light); font-size:0.85rem; color:var(--text-muted);">
            ℹ️ المحاصيل المرشحة: <strong>${multiSeasonState.candidateCrops.map(c => getCropDisplayName(c)).join(", ")}</strong>
            <button onclick="renderMultiSeasonStep1()" style="border:none; background:none; color:var(--primary-green); cursor:pointer; text-decoration:underline; font-weight:700; margin-right:6px;">(تعديل)</button>
          </div>
        </div>
      </div>

      <!-- Previous Crops History Preview -->
      <div style="background:var(--bg-subtle); padding:16px; border-radius:12px; border:1px solid var(--border-color);">
        <h4 style="color:var(--primary-nile); margin-bottom:10px;">📜 سجل المحصول السابق لكل أرض (تلقائي من الخطة السابقة)</h4>
        <div style="display:flex; flex-direction:column; gap:8px;">
          ${prevCropsHtml}
        </div>
      </div>

      <!-- Budget Carry-Forward & Edit Controls -->
      <div style="background:var(--bg-subtle); padding:16px; border-radius:12px; border:1px solid var(--border-color);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
          <h4 style="color:var(--primary-nile);">💧 الميزانية المنقولة تلقائياً من الموسم السابق</h4>
          <span style="font-size:0.8rem; background:var(--success-bg); color:var(--success-text); padding:4px 10px; border-radius:20px; font-weight:700;">استخدام ميزانية الموسم السابق (متاح التعديل)</span>
        </div>

        <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:12px;">
          <div>
            <label style="display:block; font-size:0.85rem; font-weight:700;">💧 ميزانية المياه (م³):</label>
            <input type="number" id="ms-water-budget" class="text-input" value="${multiSeasonState.waterBudget}" style="width:100%;">
          </div>
          <div>
            <label style="display:block; font-size:0.85rem; font-weight:700;">👷 ساعات العمل (ساعة):</label>
            <input type="number" id="ms-labor-budget" class="text-input" value="${multiSeasonState.laborBudget}" style="width:100%;">
          </div>
          <div>
            <label style="display:block; font-size:0.85rem; font-weight:700;">🧪 كمية السماد (كجم):</label>
            <input type="number" id="ms-fert-budget" class="text-input" value="${multiSeasonState.fertilizerBudget}" style="width:100%;">
          </div>
        </div>
      </div>

      <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid var(--border-color); padding-top:16px;">
        <button class="btn btn-secondary" onclick="renderMultiSeasonStep1()">← التعديل في القائمة</button>
        <button class="btn btn-primary" onclick="executeMultiSeasonPlan()" style="background:linear-gradient(135deg, #1b4332, #2d6a4f); font-weight:700; padding:12px 24px;">
          <span>بدء التخطيط للموسم القادم 🚀</span>
        </button>
      </div>

    </div>
  `;
}

function executeMultiSeasonPlan() {
  // Read season from the dropdown (farmer may override the default)
  const seasonSelect = document.getElementById("ms-season-select");
  const seasonName = seasonSelect ? seasonSelect.value : multiSeasonState.currentSeasonName;

  const waterBudget = parseFloat(document.getElementById("ms-water-budget").value) || multiSeasonState.waterBudget;
  const laborBudget = parseFloat(document.getElementById("ms-labor-budget").value) || multiSeasonState.laborBudget;
  const fertBudget = parseFloat(document.getElementById("ms-fert-budget").value) || multiSeasonState.fertilizerBudget;

  fetch("/api/multi-season/next-season", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: multiSeasonState.sessionId,
      season_name: seasonName,
      water_budget: waterBudget,
      labor_budget: laborBudget,
      fertilizer_budget: fertBudget,
    }),
  })
    .then(res => res.json())
    .then(data => {
      if (data.detail) {
        alert("خطأ: " + data.detail);
        return;
      }

      multiSeasonState.currentPlan = data;
      multiSeasonState.currentPreviousCrops = data.next_previous_crops;
      multiSeasonState.waterBudget = data.water_budget;
      multiSeasonState.laborBudget = data.labor_budget;
      multiSeasonState.fertilizerBudget = data.fertilizer_budget;

      if (!multiSeasonState.seasonHistory) multiSeasonState.seasonHistory = [];
      multiSeasonState.seasonHistory.push(data);

      // Only advance the W⇔S tracker when a main season was planned.
      // If farmer chose Nili, keep currentSeasonName unchanged so the next
      // dropdown still auto-selects the correct alternating main season.
      if (seasonName !== "Nili") {
        multiSeasonState.currentSeasonName = seasonName;
      }

      renderMultiSeasonStep3();
    })
    .catch(err => {
      console.error("Error generating season plan:", err);
      alert("حدث خطأ أثناء الاتصال بالمخدم لتوليد الخطة.");
    });
}

// STEP 3: Season Results & Financial Projection View
function renderMultiSeasonStep3() {
  multiSeasonState.step = 3;
  const modalTitle = document.getElementById("ms-modal-title");
  const modalBody = document.getElementById("ms-modal-body");
  const plan = multiSeasonState.currentPlan;

  if (!plan) return;

  modalTitle.innerHTML = `✅ نتيجة تخطيط الموسم: ${escapeHtml(plan.season_name)} (موسم رقم ${plan.season_number})`;

  // Field allocation rows
  let allocRowsHtml = "";
  for (const [fName, cMap] of Object.entries(plan.crop_allocation)) {
    const finFieldMap = plan.field_financials[fName] || {};
    for (const [cName, ha] of Object.entries(cMap)) {
      if (ha <= 0) continue;
      const fin = finFieldMap[cName] || {};
      const arCrop = getCropDisplayName(cName);
      const prevC = getCropDisplayName(plan.previous_crops[fName] || "لا يوجد");

      allocRowsHtml += `
        <tr style="border-bottom:1px solid var(--border-color);">
          <td style="padding:10px; font-weight:700;">${escapeHtml(fName)}</td>
          <td style="padding:10px; color:var(--text-muted);">${escapeHtml(prevC)}</td>
          <td style="padding:10px; font-weight:700; color:var(--primary-nile);">${escapeHtml(arCrop)}</td>
          <td style="padding:10px; text-align:center;">${ha.toFixed(2)} هكتار</td>
          <td style="padding:10px; text-align:center; color:var(--primary-green); font-weight:700;">${(fin.expected_revenue || 0).toLocaleString()} EGP</td>
          <td style="padding:10px; text-align:center; color:var(--danger-text);">${(fin.total_cost || 0).toLocaleString()} EGP</td>
          <td style="padding:10px; text-align:center; color:var(--primary-nile); font-weight:800;">${(fin.net_profit || 0).toLocaleString()} EGP</td>
          <td style="padding:10px; text-align:center; font-weight:700;">${(fin.profit_margin * 100 || 0).toFixed(1)}%</td>
        </tr>
      `;
    }
  }

  const finSum = plan.financial_summary || {};

  modalBody.innerHTML = `
    <div style="display:flex; flex-direction:column; gap:20px;">
      
      <!-- Financial & Resource Summary KPI Grid -->
      <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:12px;">
        <div style="background:var(--gold-bg); border:1px solid var(--gold-light); padding:12px; border-radius:10px; text-align:center;">
          <div style="font-size:0.8rem; color:var(--gold-accent); font-weight:700;">إجمالي الربح الصافي</div>
          <div style="font-size:1.3rem; font-weight:800; color:var(--primary-nile);">${(finSum.total_expected_net_profit || 0).toLocaleString()} EGP</div>
        </div>
        <div style="background:var(--bg-subtle); border:1px solid var(--border-color); padding:12px; border-radius:10px; text-align:center;">
          <div style="font-size:0.8rem; color:var(--text-muted);">إجمالي الإيرادات</div>
          <div style="font-size:1.1rem; font-weight:700;">${(finSum.total_expected_revenue || 0).toLocaleString()} EGP</div>
        </div>
        <div style="background:var(--bg-subtle); border:1px solid var(--border-color); padding:12px; border-radius:10px; text-align:center;">
          <div style="font-size:0.8rem; color:var(--text-muted);">إجمالي التكاليف</div>
          <div style="font-size:1.1rem; font-weight:700; color:var(--danger-text);">${(finSum.total_cost || 0).toLocaleString()} EGP</div>
        </div>
        <div style="background:var(--bg-subtle); border:1px solid var(--border-color); padding:12px; border-radius:10px; text-align:center;">
          <div style="font-size:0.8rem; color:var(--text-muted);">هامش الربح الإجمالي</div>
          <div style="font-size:1.1rem; font-weight:700; color:var(--primary-green);">${(finSum.overall_profit_margin_pct || 0)}%</div>
        </div>
      </div>

      <!-- Allocations Table -->
      <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:12px; padding:16px;">
        <h4 style="color:var(--primary-nile); margin-bottom:12px;">📍 التوزيع الزراعي الموصى به والأرباح التقديرية للموسم</h4>
        <div style="overflow-x:auto;">
          <table style="width:100%; border-collapse:collapse; font-size:0.9rem;">
            <thead>
              <tr style="background:var(--bg-subtle); text-align:right;">
                <th style="padding:10px;">الأرض</th>
                <th style="padding:10px;">المحصول السابق</th>
                <th style="padding:10px;">المحصول الموصى به</th>
                <th style="padding:10px; text-align:center;">المساحة</th>
                <th style="padding:10px; text-align:center;">الإيراد المتوقع</th>
                <th style="padding:10px; text-align:center;">إجمالي التكلفة</th>
                <th style="padding:10px; text-align:center;">صافي الربح</th>
                <th style="padding:10px; text-align:center;">هامش الربح</th>
              </tr>
            </thead>
            <tbody>
              ${allocRowsHtml || '<tr><td colspan="8" style="text-align:center; padding:20px;">لم يتم تخصيص محاصيل لمحدودية الميزانية.</td></tr>'}
            </tbody>
          </table>
        </div>
      </div>

      <!-- Bottom Action Bar -->
      <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid var(--border-color); padding-top:16px;">
        <button class="btn btn-secondary" onclick="renderMultiSeasonStep1()">تعديل المحاصيل المرشحة ✏️</button>
        <button class="btn btn-primary" onclick="advanceToFollowingSeason()" style="background:linear-gradient(135deg, #1b4332, #2d6a4f); font-weight:800; padding:12px 24px;">
          <span>التخطيط للموسم التالي ➔</span>
        </button>
      </div>

    </div>
  `;
}

function advanceToFollowingSeason() {
  // currentSeasonName already records the season just planned. The setup
  // renderer derives and selects the immediately following season from it.
  renderMultiSeasonStep2();
}

