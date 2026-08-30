"""LLM Explanation Service for Crop Mix Business Planner.

Uses Gemini API (or OpenAI / rule-based fallback) to generate natural, human-understandable
agronomic explanations for why a specific crop mix allocation was chosen by the optimization model.
"""

import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from pathlib import Path

# Load .env file if present
def load_env_file():
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip().strip("'").strip('"')
        except Exception:
            pass

load_env_file()


class CropMixLLMExplainer:
    """Generates agronomic explanations for crop optimization results using LLM."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")
        try:
            from crop_mix.data.rotation_loader import RotationMatrixLoader
            self.arabic_map = RotationMatrixLoader().arabic_map
        except Exception:
            self.arabic_map = {}

    def get_ar_crop(self, name: Optional[str]) -> str:
        if not name or name == "None" or name == "none":
            return "لا يوجد"
        return self.arabic_map.get(name, name)

    def generate_explanation(self, opt_result: Dict[str, Any], lang: str = "ar") -> Dict[str, Any]:
        """Generate LLM-driven explanation for the optimization plan.

        Args:
            opt_result: Dictionary of optimization results from /api/optimize endpoint.
            lang: Language string ('ar' for Arabic, 'en' for English).

        Returns:
            Dict with 'explanation_markdown', 'key_reasons', and 'provider'.
        """
        # Ensure env is reloaded if set dynamically
        if not self.api_key:
            self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")

        prompt = self._build_prompt(opt_result, lang=lang)

        if self.api_key:
            llm_text = self._call_gemini_api(prompt)
            if llm_text:
                return {
                    "explanation_markdown": llm_text,
                    "provider": "Gemini AI",
                    "status": "success",
                }

        # Fallback if no API key or call fails
        fallback_text = self._generate_agronomic_fallback(opt_result, lang=lang)
        return {
            "explanation_markdown": fallback_text,
            "provider": "Agronomic Synthesis Engine (Fallback)",
            "status": "fallback",
        }

    def _call_gemini_api(self, prompt: str) -> Optional[str]:
        """Call Gemini REST API directly using urllib with model fallback."""
        models_to_try = [
            "gemini-1.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-pro",
        ]

        for model_name in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 1500,
                    }
                }

                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
                with urllib.request.urlopen(req, timeout=10) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    candidates = res_data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()

            except Exception as exc:
                continue

        # SDK Fallback
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception:
            pass

        return None

    def get_field_disqualification_details(self, res: Dict[str, Any], f_name: str, lang: str = "ar") -> List[str]:
        """Extract exact, specific disqualification reasons for a field from suitability & rotation details."""
        reasons = []
        suitability = res.get("suitability_details", [])
        rotation = res.get("rotation_details", [])
        prev_crops = res.get("field_previous_crops", {})
        prev_c_raw = prev_crops.get(f_name)
        prev_c_ar = self.get_ar_crop(prev_c_raw)

        # 1. Rotation constraints check
        disallowed_rotations = [item for item in rotation if item.get("field") == f_name and not item.get("suitable")]
        if disallowed_rotations:
            if prev_c_raw and str(prev_c_raw).strip() not in ("None", "none", ""):
                reasons.append(
                    f"حظر الدورة الزراعية: المحصول السابق في الأرض هو ({prev_c_ar})، وقواعد التتابع الزراعي المصري تمنع زراعة المحاصيل المتاحة بعده."
                    if lang == "ar" else
                    f"Rotation Restriction: Previous crop was ({prev_c_raw}), which is disallowed before available candidate crops."
                )

        # 2. Soil chemistry (pH, EC, texture) check
        unsuitable_soil = [item for item in suitability if item.get("field") == f_name and not item.get("suitable")]
        if unsuitable_soil:
            soil_issues = []
            for item in unsuitable_soil:
                crop_ar = self.get_ar_crop(item.get("crop"))
                reason_text = item.get("reason", "")
                if lang == "ar":
                    reason_text = (
                        reason_text
                        .replace("pH", "حموضة pH")
                        .replace("Salinity EC", "ملوحة EC")
                        .replace("Texture", "قوام التربة")
                        .replace("not in suitable list", "غير مناسب")
                        .replace("< min required", "أقل من الحد الأدنى المقبول")
                        .replace("> max tolerated", "أعلى من الحد الأقصى المتحمل")
                    )
                    soil_issues.append(f"المحصول {crop_ar}: {reason_text}")
                else:
                    soil_issues.append(f"Crop {item.get('crop')}: {reason_text}")

            if soil_issues:
                reasons.append(
                    "عدم ملاءمة التربة: " + "؛ ".join(soil_issues[:3])
                    if lang == "ar" else
                    "Soil Chemistry Incompatibility: " + "; ".join(soil_issues[:3])
                )

        return reasons


    def _build_prompt(self, res: Dict[str, Any], lang: str = "ar") -> str:
        """Construct structured prompt for LLM grounded strictly in input data."""
        version = res.get("version", "V4")
        profit = res.get("expected_profit", 0)
        revenue = res.get("total_expected_revenue", 0)
        prod_cost = res.get("total_production_cost", 0)
        labor_cost = res.get("total_labor_cost", 0)
        fert_cost = res.get("total_fertilizer_cost", 0)
        total_land = res.get("total_land_used", 0)
        land_limit = res.get("field_area_limit", 0)
        unused_land = max(0.0, land_limit - total_land)

        alloc_summary = res.get("crop_allocation_summary", {})
        field_allocs = res.get("field_allocations", {})
        binding = res.get("binding_constraints", [])
        suitability = res.get("suitability_details", [])
        rotation = res.get("rotation_details", [])
        prev_crops = res.get("field_previous_crops", {})

        binding_str = ", ".join([f"{b['resource']} ({b['utilization_pct']}%)" for b in binding if b.get("is_binding")]) or "لا توجد قيود اختناق"

        if lang == "ar":
            # Translate previous crops and allocations to Arabic
            prev_crops_ar = {f: self.get_ar_crop(c) for f, c in prev_crops.items()}
            field_allocs_ar = {}
            for f, allocs in field_allocs.items():
                field_allocs_ar[f] = {self.get_ar_crop(c): feddans for c, feddans in allocs.items() if feddans > 0}

            prompt = f"""
أنت مهندس زراعي ومستشار اقتصادي للمزارع المصري. قم بتحليل التوزيع المحصولي التالي الناتج عن نموذج التحسين الرياضي واشرح للمزارع بلغة عربية واضحة ومبسطة ومستندة تماماً إلى البيانات المدخلة:

⚠️ **تعليمات صارمة**:
1. اكتب كافة أسماء المحاصيل باللغة العربية الفصحى والمصرية دائماً (مثل: قمح، فول صويا، طماطم، ذرة صفراء، قطن، بصل كامل النضج) ولا تذكر اسم أي محصول باللغة الإنجليزية مطلقاً.
2. استخدم وحدة 'فدان' دائماً للأراضي ولا تستخدم وحدة 'هكتار' إطلاقاً.

### 📊 بيانات المزرعة والنتائج الرياضية:
- إصدار المحرك: {version}
- إجمالي مساحة الأراضي المتاحة: {land_limit} فدان
- المساحة المزروعة بالفعل: {total_land} فدان (المساحة المتروكة بدون زراعة: {unused_land} فدان)
- الربح الصافي المتوقع: {profit:,.0f} ج.م
- الإيرادات الإجمالية: {revenue:,.0f} ج.م
- التكاليف الإجمالية: {prod_cost + labor_cost + fert_cost:,.0f} ج.م
- القيود الحاكمة المكتملة 100% (العنق الزجاجي Binding Constraints): {binding_str}

### 📍 المحاصيل السابقة والتوزيع الحالي لكل قطعة أرض:
- المحاصيل السابقة للأراضي: {json.dumps(prev_crops_ar, ensure_ascii=False)}
- التوزيع التكليفي المحسوب بالفدان: {json.dumps(field_allocs_ar, ensure_ascii=False, indent=2)}

---

### 📝 المطلوب منك في التقرير (يجب الاستناد المباشر إلى البيانات المدخلة ومخرجات الملائمة أعلاه):
1. **أسباب اختيار المحصول لكل أرض بالتحديد**: اشرح بالتفصيل لماذا تم تخصيص هذا المحصول لهذه القطعة بالتحديد (ملاءمة pH، EC، نوع التربة، والمحصول السابق وفقاً لقواعد الدورة الزراعية المصرية).
2. **السبب المباشر والمحدد لترك الأراضي بور**:
   - إذا كانت هناك مساحة غير مزروعة ({unused_land} فدان)، اذكر السبب المباشر والمحدد جداً لكل أرض بناءً على قيود التربة والدورة المذكورة أعلاه (مثال: "تم ترك حوض الشرقية بور لأن المحصول السابق هو أشجار المانجو وهي نبات معمر يمنع استبداله بمحاصيل موسمية حقلية، ولأن درجة الحموضة pH 5.5 أقل من المقبول لزراعة القمح والصويا والطماطم").
3. **تحليل قيود العنق الزجاجي**: وضح المورد المالي أو المائي الحاكم الذي منع زيادة الأرباح.
4. **توصيات وختام مشجع للفلاح**.

"""
        else:
            prompt = f"""
You are an agronomic engineer and farm economics advisor. Analyze the following mathematical optimization output and provide a clear, data-driven explanation for the farmer detailing WHY this specific allocation was chosen:

### 📊 Farm Data & Optimization Results:
- Model Version: {version}
- Total Available Land: {land_limit} feddans
- Total Allocated Land: {total_land} feddans (Unplanted Fallow Land: {unused_land} feddans)
- Net Expected Profit: {profit:,.0f} EGP
- Gross Revenue: {revenue:,.0f} EGP
- Operational Costs: {prod_cost + labor_cost + fert_cost:,.0f} EGP
- Binding Bottleneck Constraints: {binding_str}

### 📍 Previous Crops & Allocations per Field:
- Previous Crop History: {json.dumps(prev_crops, indent=2)}
- Calculated Allocation: {json.dumps(field_allocs, indent=2)}

### 📝 Required Sections:
1. **Per-Field Specific Justification**: Explain why each crop was assigned to each specific field based on soil pH, EC salinity, texture compatibility, previous crop rotation succession, and profit contribution.
2. **Why Full Land Was Not Planted / Why Land is Left Fallow**:
   - If {unused_land} feddans is unplanted, explicitly explain why based on input data (e.g. water budget exhausted at 100%, labor/fertilizer caps, or soil/rotation disqualifications for remaining crops).
3. **Bottleneck Resource Analysis**: Explain which resource constrained maximum returns.
4. **Encouraging Summary for Farmer**.
"""
        return prompt.strip()

    def _generate_agronomic_fallback(self, res: Dict[str, Any], lang: str = "ar") -> str:
        """Generate structured agronomic explanation text when API key is unavailable."""
        profit = res.get("expected_profit", 0)
        revenue = res.get("total_expected_revenue", 0)
        prod_cost = res.get("total_production_cost", 0)
        labor_cost = res.get("total_labor_cost", 0)
        fert_cost = res.get("total_fertilizer_cost", 0)
        total_costs = prod_cost + labor_cost + fert_cost
        total_land = res.get("total_land_used", 0)
        land_limit = res.get("field_area_limit", 0)
        unused_land = max(0.0, land_limit - total_land)

        alloc_summary = res.get("crop_allocation_summary", {})
        field_allocs = res.get("field_allocations", {})
        binding = res.get("binding_constraints", [])
        prev_crops = res.get("field_previous_crops", {})
        binding_items = [b for b in binding if b.get("is_binding")]

        if lang == "ar":
            crops_str = "، ".join([f"**{self.get_ar_crop(c)}** ({feddans:.1f} فدان)" for c, feddans in alloc_summary.items() if feddans > 0])
            
            if binding_items:
                binding_text = "، ".join([f"**{b['resource']}** ({b['utilization_pct']}%)" for b in binding_items])
                bottleneck_summary = f"العوامل الحاكمة التي حددت أقصى ربحية واستنفدت بالكامل (100%) هي: {binding_text}.\n*زيادة حصة هذه الموارد في الموسم المقبل سيتيح توسيع المساحات المزروعة وزيادة الربح الصافي.*"
            else:
                binding_text = None
                bottleneck_summary = "جميع ميزانيات الموارد المتاحة (المياه، العمالة، والسماد) كافية بالكامل ولم تشكل أي عائق أمام التخطيط."

            # Build per-field rationales in Arabic
            field_lines = []
            specific_reasons_summary = []
            for f_name, allocs in field_allocs.items():
                prev_c_raw = prev_crops.get(f_name)
                prev_c_ar = self.get_ar_crop(prev_c_raw)
                f_crops = [f"**{self.get_ar_crop(c)}** ({feddans:.1f} فدان)" for c, feddans in allocs.items() if feddans > 0]
                if f_crops:
                    field_lines.append(f"- **{f_name}** (المحصول السابق: {prev_c_ar}): تم اختيار {', '.join(f_crops)} لملاءمتها العالية لخاصية التربة وقواعد التتابع الموصى بها.")
                else:
                    spec_reasons = self.get_field_disqualification_details(res, f_name, lang="ar")
                    if spec_reasons:
                        reasons_joined = " | ".join(spec_reasons)
                        field_lines.append(f"- **{f_name}** (المحصول السابق: {prev_c_ar}): تركت أرض بور للأسباب المحددة التالية: ({reasons_joined}).")
                        specific_reasons_summary.append(f"قطعة **{f_name}**: {reasons_joined}")
                    else:
                        field_lines.append(f"- **{f_name}** (المحصول السابق: {prev_c_ar}): تركت أرض بور لتجنب تجاوز الميزانية بدون عائد مجدٍ.")
            field_breakdown_str = "\n".join(field_lines)

            # Build unplanted land rationale with exact, sound logic
            if unused_land > 0.01:
                if binding_items:
                    unplanted_reason = f"تم ترك مساحة قدرها **{unused_land:.1f} فدان** بدون زراعة (أرض بور) بسبب استنفاد ميزانية الموارد المتاحة بالكامل (100%): {binding_text}. زراعة هذه المساحة كانت ستتطلب كميات إضافية غير متاحة من المياه أو العمالة."
                else:
                    unplanted_reason = f"تم ترك مساحة قدرها **{unused_land:.1f} فدان** بدون زراعة (أرض بور) لأن المحاصيل المتاحة في القائمة غير متوافقة مع خصائص تربة هذه القطعة (درجة الحموضة pH، الملوحة EC، أو القوام) أو غير مسموح بها وفقاً لقواعد الدورة الزراعية مع المحصول السابق. زراعة محاصيل غير مناسبة كان سيتسبب في انخفاض الإنتاجية وخسارة مالية."
            else:
                unplanted_reason = "تم استغلال كامل مساحة الأراضي المتاحة بنسبة 100% وتوزيع المحاصيل بشكل مثالي دون ترك أي مساحات بور."

            return f"""### 🤖 التفسير الذكي للخطة الزراعية الموصى بها

#### 🎯 لماذا تم اختيار هذا التوزيع لكل أرض بالتحديد؟
تم حساب التوزيع الأفضل باستخدام البرمجة الخطية المستمرة للوصول لأعلى صافي ربح قدره **{profit:,.0f} ج.م**. وتوضيح الاختيار لكل قطعة أرض كالتالي:
{field_breakdown_str}

#### 🏜️ لماذا لم تزرع كامل الأرض؟ (أسباب ترك الأراضي بور)
{unplanted_reason}

#### ⚖️ التحليل المالي وتكاليف التشغيل:
- **إجمالي المبيعات الإجمالية**: {revenue:,.0f} ج.م
- **إجمالي التكاليف التشغيلية**: {total_costs:,.0f} ج.م (تكاليف زراعة: {prod_cost:,.0f} ج.م | عمالة: {labor_cost:,.0f} ج.م | سماد: {fert_cost:,.0f} ج.م)

#### ⚠️ الموارد المحددة للربح (عنق الزجاجة):
{bottleneck_summary}
"""


        else:
            crops_str = ", ".join([f"**{c}** ({feddans:.1f} feddans)" for c, feddans in alloc_summary.items() if feddans > 0])

            if binding_items:
                binding_text = ", ".join([f"**{b['resource']}** ({b['utilization_pct']}%)" for b in binding_items])
                bottleneck_summary = f"Resource bottlenecks that reached 100% capacity were: {binding_text}.\n*Increasing allocations for these bottleneck resources next season will allow for larger crop areas and higher net profits.*"
            else:
                binding_text = None
                bottleneck_summary = "All resource budgets (water, labor, fertilizer) were fully sufficient and did not constrain the plan."

            field_lines = []
            for f_name, allocs in field_allocs.items():
                prev_c = prev_crops.get(f_name) or "None"
                f_crops = [f"**{c}** ({feddans:.1f} feddans)" for c, feddans in allocs.items() if feddans > 0]
                if f_crops:
                    field_lines.append(f"- **{f_name}** (Prev: {prev_c}): Assigned {', '.join(f_crops)} due to high soil compatibility and crop rotation alignment.")
                else:
                    field_lines.append(f"- **{f_name}** (Prev: {prev_c}): Left fallow due to soil/rotation incompatibility for remaining crop options.")
            field_breakdown_str = "\n".join(field_lines)

            if unused_land > 0.01:
                if binding_items:
                    unplanted_reason = f"An area of **{unused_land:.1f} feddans** was left unplanted (fallow) because primary resource budgets ({binding_text}) were 100% exhausted."
                else:
                    unplanted_reason = f"An area of **{unused_land:.1f} feddans** was left unplanted (fallow) because remaining candidate crops were incompatible with the soil chemistry (pH, EC salinity, or texture) or barred by crop rotation rules."
            else:
                unplanted_reason = "100% of available land was fully allocated across fields with zero fallow area."

            return f"""### 🤖 Smart Plan Explanation

#### 🎯 Per-Field Crop Allocation Justification:
The continuous LP solver maximized farm profit to **{profit:,.0f} EGP**. Breakdown by field:
{field_breakdown_str}

#### 🏜️ Why Full Land Was Not Planted (Fallow Land Analysis):
{unplanted_reason}

#### ⚖️ Financial Breakdown:
- **Gross Revenue**: {revenue:,.0f} EGP
- **Total Operational Costs**: {total_costs:,.0f} EGP (Production: {prod_cost:,.0f} EGP | Labor: {labor_cost:,.0f} EGP | Fertilizer: {fert_cost:,.0f} EGP)

#### ⚠️ Bottleneck Constraint Analysis:
{bottleneck_summary}
"""


