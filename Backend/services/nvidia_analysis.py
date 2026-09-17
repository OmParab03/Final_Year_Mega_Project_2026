# -*- coding: utf-8 -*-
# services/nvidia_analysis.py
# ─────────────────────────────────────────────────────────────────────────────
# Robust Product Ingredient Analysis Service
# Uses NVIDIA LLaMA Vision API + local safety rules for medical-grade output.
# ─────────────────────────────────────────────────────────────────────────────
import os
import re
import base64
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# HARDCODED SAFETY KNOWLEDGE BASE
# These rules supplement AI output with clinically known facts.
# ─────────────────────────────────────────────────────────────────────────────

# Ingredients that are COMEDOGENIC (pore-clogging), especially harmful for
# acne-prone / oily skin
COMEDOGENIC_INGREDIENTS = {
    "isopropyl myristate", "isopropyl palmitate", "isopropyl isostearate",
    "coconut oil", "cocoa butter", "wheat germ oil", "flaxseed oil",
    "algae extract", "sodium lauryl sulfate", "sls", "lanolin",
    "acetylated lanolin", "petrolatum", "mineral oil", "lauric acid",
    "myristic acid", "myristyl myristate", "oleic acid",
    "butyl stearate", "decyl oleate", "octyl stearate",
}

# Known common allergens and irritants
KNOWN_ALLERGENS_IRRITANTS = {
    "fragrance", "parfum", "linalool", "limonene", "citronellol",
    "geraniol", "eugenol", "cinnamal", "isoeugenol", "benzyl alcohol",
    "benzyl benzoate", "benzyl cinnamate", "benzyl salicylate",
    "coumarin", "alpha-isomethyl ionone", "amyl cinnamal",
    "hexyl cinnamal", "anise alcohol", "farnesol", "citral",
    "methyl 2-octynoate", "hydroxycitronellal", "formaldehyde",
    "quaternium-15", "dmdm hydantoin", "imidazolidinyl urea",
    "diazolidinyl urea", "methylisothiazolinone", "mit",
    "methylchloroisothiazolinone", "mcit", "benzisothiazolinone",
    "propylene glycol", "parabens", "methylparaben", "propylparaben",
    "butylparaben", "ethylparaben", "kathon cg", "phenoxyethanol",
    "bronopol", "2-bromo-2-nitropropane-1,3-diol",
}

# Ingredients harmful for specific skin types
SKIN_TYPE_RULES = {
    "dry": {
        "avoid": {
            "alcohol denat", "sd alcohol", "alcohol", "witch hazel",
            "salicylic acid", "benzoyl peroxide", "retinol", "glycolic acid",
            "lactic acid", "sodium lauryl sulfate", "sls",
        },
        "beneficial": {
            "glycerin", "hyaluronic acid", "ceramide", "niacinamide",
            "shea butter", "jojoba oil", "squalane", "panthenol",
            "aloe vera", "urea", "allantoin", "vitamin e", "tocopherol",
        }
    },
    "oily": {
        "avoid": {
            "coconut oil", "cocoa butter", "mineral oil", "petrolatum",
            "lanolin", "isopropyl myristate", "shea butter", "beeswax",
        },
        "beneficial": {
            "niacinamide", "salicylic acid", "zinc pca", "tea tree oil",
            "glycolic acid", "benzoyl peroxide", "green tea extract",
            "hyaluronic acid", "glycerin",
        }
    },
    "combination": {
        "avoid": {
            "heavy oils", "lanolin", "mineral oil", "petrolatum",
        },
        "beneficial": {
            "niacinamide", "hyaluronic acid", "glycerin", "salicylic acid",
            "green tea extract", "aloe vera",
        }
    },
    "sensitive": {
        "avoid": {
            "fragrance", "parfum", "alcohol denat", "sd alcohol",
            "sodium lauryl sulfate", "retinol", "glycolic acid",
            "benzoyl peroxide", "alpha hydroxy acids", "essential oils",
        },
        "beneficial": {
            "aloe vera", "chamomile", "oat extract", "centella asiatica",
            "panthenol", "allantoin", "ceramide", "glycerin",
        }
    }
}

# Age-specific warnings
AGE_RULES = {
    "retinol":          {"min_age": 25, "reason": "Retinol is too harsh for skin under 25, may cause irritation."},
    "tretinoin":        {"min_age": 18, "reason": "Tretinoin is prescription-strength, not recommended under 18."},
    "benzoyl peroxide": {"max_age": 45, "reason": "Benzoyl peroxide may over-dry mature skin over 45."},
    "glycolic acid":    {"min_age": 16, "reason": "High-strength AHAs not recommended for very young skin."},
    "kojic acid":       {"min_age": 18, "reason": "Kojic acid can be sensitizing for skin under 18."},
}


def _get_skin_type_key(skin_type_str: str) -> str:
    """Normalize skin type string to a key in SKIN_TYPE_RULES."""
    if not skin_type_str:
        return ""
    s = skin_type_str.lower()
    if "dry" in s:
        return "dry"
    if "oily" in s:
        return "oily"
    if "combination" in s:
        return "combination"
    if "sensitive" in s:
        return "sensitive"
    return ""


def _apply_safety_rules(result: dict, user_profile: dict) -> dict:
    """
    Post-process the AI result with hardcoded safety rules.
    This ensures that even if the AI misses something, known hazards are flagged.
    """
    age       = user_profile.get('age')
    skin_type = _get_skin_type_key(user_profile.get('skinType', ''))
    allergies = [a.lower().strip() for a in user_profile.get('allergies', [])]
    condition = (user_profile.get('skin_condition') or '').lower()

    # Collect ingredient names already flagged by AI (to avoid duplicates)
    already_harmful    = {i['name'].lower() for i in result.get('harmful_ingredients', [])}
    already_beneficial = {i['name'].lower() for i in result.get('beneficial_ingredients', [])}
    all_ingredients    = already_harmful | already_beneficial

    extra_harmful    = []
    extra_beneficial = []
    allergy_warnings = []

    for ing_name_lower in all_ingredients:

        # ── 1. ALLERGY CHECK (highest priority) ──
        for allergen in allergies:
            if allergen and (allergen in ing_name_lower or ing_name_lower in allergen):
                allergy_warnings.append({
                    "name":   ing_name_lower.title(),
                    "reason": f"⚠️ ALLERGY ALERT: You have listed '{allergen}' as a known allergy. This ingredient may trigger an allergic reaction — avoid this product.",
                    "risk":   "High"
                })
                # If AI marked it beneficial, remove that
                result['beneficial_ingredients'] = [
                    i for i in result.get('beneficial_ingredients', [])
                    if i['name'].lower() != ing_name_lower
                ]
                break

        # ── 2. KNOWN ALLERGEN / IRRITANT CHECK ──
        for irritant in KNOWN_ALLERGENS_IRRITANTS:
            if irritant in ing_name_lower and ing_name_lower not in already_harmful:
                extra_harmful.append({
                    "name":   ing_name_lower.title(),
                    "reason": f"Known common irritant/allergen. May cause sensitization, redness, or reaction in reactive skin.",
                    "risk":   "Medium"
                })
                break

        # ── 3. COMEDOGENIC CHECK for acne / oily skin ──
        is_acne_prone = "acne" in condition or skin_type == "oily"
        for comed in COMEDOGENIC_INGREDIENTS:
            if comed in ing_name_lower and is_acne_prone and ing_name_lower not in already_harmful:
                extra_harmful.append({
                    "name":   ing_name_lower.title(),
                    "reason": f"Comedogenic ingredient. Can clog pores and worsen acne/breakouts for {'acne-prone' if 'acne' in condition else 'oily'} skin.",
                    "risk":   "High" if "acne" in condition else "Medium"
                })
                break

        # ── 4. SKIN TYPE RULE CHECK ──
        if skin_type and skin_type in SKIN_TYPE_RULES:
            rules = SKIN_TYPE_RULES[skin_type]
            for avoid_ing in rules["avoid"]:
                if avoid_ing in ing_name_lower and ing_name_lower not in already_harmful:
                    extra_harmful.append({
                        "name":   ing_name_lower.title(),
                        "reason": f"Not recommended for {skin_type} skin. Can exacerbate {skin_type} skin conditions.",
                        "risk":   "Medium"
                    })
                    break
            for good_ing in rules["beneficial"]:
                if good_ing in ing_name_lower and ing_name_lower not in already_beneficial:
                    extra_beneficial.append({
                        "name":   ing_name_lower.title(),
                        "reason": f"Excellent choice for {skin_type} skin. Helps balance and improve skin barrier.",
                        "rating": "Good"
                    })
                    break

        # ── 5. AGE-SPECIFIC CHECK ──
        if age and isinstance(age, (int, float)):
            for age_ing, age_rule in AGE_RULES.items():
                if age_ing in ing_name_lower:
                    min_age = age_rule.get("min_age", 0)
                    max_age = age_rule.get("max_age", 120)
                    if age < min_age or age > max_age:
                        if ing_name_lower not in already_harmful:
                            extra_harmful.append({
                                "name":   ing_name_lower.title(),
                                "reason": f"Age consideration (you are {age}): {age_rule['reason']}",
                                "risk":   "Medium"
                            })

    # Prepend allergy warnings (highest priority — shown first)
    result['harmful_ingredients'] = allergy_warnings + result.get('harmful_ingredients', []) + extra_harmful
    result['beneficial_ingredients'] = result.get('beneficial_ingredients', []) + extra_beneficial

    # Recalculate score if allergy warnings were added
    if allergy_warnings:
        result['score'] = max(0, result.get('score', 50) - 30 * len(allergy_warnings))
        result['score_label'] = "Not Recommended"
        result['score_summary'] = f"This product contains {len(allergy_warnings)} ingredient(s) that match your known allergies. Avoid use."

    return result


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def _extract_ai_summary_from_raw(text: str) -> str:
    """
    Attempt to extract ai_summary from ANY text — works on both valid JSON,
    truncated JSON, and markdown prose. Returns empty string if nothing found.
    """
    # 1. Try JSON key extraction (handles truncated JSON too)
    m = re.search(r'["\']ai_summary["\']\s*:\s*["\']([^\'"]{20,})', text, re.IGNORECASE | re.DOTALL)
    if m:
        # Clean up escaped characters
        summary = m.group(1)
        # Cut off at the next unescaped quote
        end_match = re.search(r'(?<!\\)["\']', summary)
        if end_match:
            summary = summary[:end_match.start()]
        summary = summary.replace('\\n', ' ').replace('\\"', '"').replace("\\'", "'").strip()
        if len(summary) > 20:
            return summary

    # 2. Try prose patterns
    for pattern in [
        r'AI Summary[^:]*:\s*(.*?)(?:\n\n|\*\*|$)',
        r'In conclusion[,:]?\s*(.*?)(?:\n\n|$)',
        r'Overall[,:]?\s*(.*?(?:skin|product|ingredient).*?)(?:\n\n|$)',
        r'summary[^:]*:\s*(.*?)(?:\n\n|\*\*|$)',
    ]:
        m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if m:
            candidate = m.group(1).strip()
            if len(candidate) > 20:
                return candidate[:500]

    return ""


def _parse_markdown_response(text: str, user_profile: dict) -> dict:
    """
    Fallback parser: model returned prose instead of JSON.
    Extract structured data using regex, then apply safety rules.
    """
    result = {
        "score": 65,
        "score_label": "Moderate Match",
        "score_summary": "Analysis extracted from AI response.",
        "harmful_ingredients": [],
        "beneficial_ingredients": [],
        "ai_summary": "",
        "potential_issues": {"dryness": 40, "irritation": 40, "pore_clogging": 30},
        "recommended_alternatives": []
    }

    # Score
    score_match = re.search(r'(?:compatibility\s+)?score[^\d]*(\d{1,3})', text, re.IGNORECASE)
    if score_match:
        s = int(score_match.group(1))
        result["score"] = s
        result["score_label"] = (
            "Excellent Match" if s >= 85 else
            "Good Match"      if s >= 70 else
            "Moderate Match"  if s >= 50 else
            "Poor Match"
        )
        result["score_summary"] = f"Compatibility score of {s}/100 personalised for your skin profile."

    # AI Summary — use the robust extractor
    result["ai_summary"] = _extract_ai_summary_from_raw(text)

    # Potential issues
    for key, pat in [("dryness", r"[Dd]ryness[:\s*]*(\d+)"), ("irritation", r"[Ii]rritation[:\s*]*(\d+)"), ("pore_clogging", r"[Pp]ore[_ ][Cc]logging[:\s*]*(\d+)")]:
        m = re.search(pat, text)
        if m:
            result["potential_issues"][key] = int(m.group(1))

    def _parse_ingredient_section(section_text):
        items = []
        # Match "* **Name**: reason" or "* Name: reason" patterns
        for pat in [r'\*\s+\*\*([^*]+)\*\*[:\s]+(.*?)(?=\n\s*\*|\Z)', r'\*\s+([^:*\n]{3,60})[:\s]+(.*?)(?=\n\s*\*|\Z)']:
            found = re.findall(pat, section_text, re.DOTALL)
            if found:
                for name, reason in found:
                    name = name.strip().strip('*').strip()
                    reason = reason.strip()
                    if name and len(name) > 2:
                        items.append((name, reason[:250]))
                break
        return items

    # Harmful section
    harm_match = re.search(r'(?:Caution|Harmful|Avoid)[^:]*Ingredients?[:\s]*(.*?)(?=(?:Beneficial|Suitable|Safe|Recommended|AI Summary|Potential Issues)|$)', text, re.IGNORECASE | re.DOTALL)
    if harm_match:
        for name, reason in _parse_ingredient_section(harm_match.group(1)):
            risk = "High" if any(w in reason.lower() for w in ["severe", "dangerous", "allerg", "very high"]) else \
                   "Low"  if any(w in reason.lower() for w in ["mild", "minor", "low"]) else "Medium"
            result["harmful_ingredients"].append({"name": name, "reason": reason, "risk": risk})

    # Beneficial section
    bene_match = re.search(r'(?:Beneficial|Suitable|Safe)[^:]*Ingredients?[:\s]*(.*?)(?=(?:Caution|Harmful|Avoid|AI Summary|Potential Issues|Recommended)|$)', text, re.IGNORECASE | re.DOTALL)
    if bene_match:
        for name, reason in _parse_ingredient_section(bene_match.group(1)):
            rating = "Excellent" if any(w in reason.lower() for w in ["excellent", "highly", "very effective"]) else \
                     "Moderate"  if any(w in reason.lower() for w in ["moderate", "mild benefit"]) else "Good"
            result["beneficial_ingredients"].append({"name": name, "reason": reason, "rating": rating})

    # Alternatives
    alt_match = re.search(r'Recommended[^:]*Alternatives?[:\s]*(.*?)(?=\n\n[A-Z]|In conclusion|$)', text, re.IGNORECASE | re.DOTALL)
    if alt_match:
        alts = re.findall(r'\*\s+([^\n*]+)', alt_match.group(1))
        result["recommended_alternatives"] = [a.strip() for a in alts if a.strip()][:6]

    # Apply safety rules even on markdown fallback
    return _apply_safety_rules(result, user_profile)


def analyze_product_image(image_path: str, user_profile: dict) -> dict:
    """
    Analyze a product ingredient label image against the user's dermatological profile.

    user_profile dict keys:
      age (int | None), skinType (str), allergies (list[str]),
      skin_condition (str), conditions (list[dict])
    """
    nvidia_api_key = os.getenv("NVIDIA_API_KEY")
    if not nvidia_api_key:
        raise ValueError("NVIDIA_API_KEY is not set in environment variables.")

    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=nvidia_api_key)
    base64_image = encode_image(image_path)

    # ── Build rich user context string ──────────────────────────────────────
    age          = user_profile.get('age')
    skin_type    = user_profile.get('skinType') or 'Unknown'
    allergies    = user_profile.get('allergies') or []
    skin_cond    = user_profile.get('skin_condition') or 'None'
    ai_conditions = user_profile.get('conditions') or []

    # Merge manually set condition with AI-detected conditions
    all_conditions = []
    if skin_cond and skin_cond.lower() not in ('none', 'none / maintenance', ''):
        all_conditions.append(skin_cond)
    for c in ai_conditions:
        label = c.get('label', '')
        if label and label not in all_conditions:
            all_conditions.append(label)
    conditions_str = ', '.join(all_conditions) or 'None'

    allergy_str = ', '.join(allergies) if allergies else 'None reported'
    age_str = str(age) if age else 'Not provided'

    # Age-specific concerns
    age_notes = ""
    if age:
        if age < 18:
            age_notes = "CRITICAL: This user is under 18. Avoid recommending retinoids, strong acids (>2% AHA/BHA), or hormone-disrupting ingredients."
        elif age < 25:
            age_notes = "User is young adult (18-25). Gentle ingredients preferred. Retinol can be used at low concentrations."
        elif age < 40:
            age_notes = "Adult skin (25-40). Standard ingredient guidelines apply."
        elif age < 55:
            age_notes = "Mature adult (40-55). Anti-aging ingredients like retinol, peptides, antioxidants are beneficial. Avoid very drying formulas."
        else:
            age_notes = "Senior skin (55+). Prioritise deeply hydrating, barrier-repairing ingredients. Strong exfoliants can be over-drying."

    # Skin-type specific concerns
    skin_notes = {
        "dry":         "AVOID: Alcohol denat, SLS, high-strength AHAs. FAVOUR: Ceramides, hyaluronic acid, glycerin, shea butter.",
        "oily":        "AVOID: Heavy oils (coconut, cocoa butter), lanolin, petrolatum. FAVOUR: Niacinamide, salicylic acid, zinc, lightweight humectants.",
        "combination": "AVOID: Very heavy emollients on T-zone areas. FAVOUR: Balanced humectants, niacinamide.",
        "sensitive":   "AVOID: All fragrances, alcohol, essential oils, SLS, retinol, strong AHAs. FAVOUR: Centella asiatica, oat extract, ceramides, allantoin.",
        "acne":        "AVOID: Comedogenic oils, SLS, heavy occlusive agents. FAVOUR: Salicylic acid, benzoyl peroxide (2.5%), niacinamide, tea tree."
    }.get(skin_type.lower(), "")

    # Condition-specific concerns
    cond_notes = []
    if "acne" in conditions_str.lower():
        cond_notes.append("User has ACNE: Flag all comedogenic ingredients (isopropyl myristate, coconut oil, etc.) as HIGH risk. Prioritise salicylic acid, niacinamide.")
    if "redness" in conditions_str.lower() or "rosacea" in conditions_str.lower():
        cond_notes.append("User has REDNESS/ROSACEA: Flag fragrances, alcohol, menthol, peppermint, witch hazel as HIGH risk. Favour calming ingredients.")
    if "pigmentation" in conditions_str.lower():
        cond_notes.append("User has PIGMENTATION: Favour vitamin C, niacinamide, kojic acid, arbutin. Flag ingredients that cause photosensitivity without SPF.")
    cond_notes_str = ' | '.join(cond_notes) if cond_notes else ""

    # ── Build the system + user prompt ──────────────────────────────────────
    system_message = (
        "You are a clinical-grade AI dermatologist and cosmetic chemist. "
        "Your analysis must be medically accurate, specific to the user's profile, "
        "and detailed enough for a consumer to make an informed health decision. "
        "Never provide generic analysis — every ingredient assessment must explain "
        "WHY it is safe or harmful specifically for THIS user's skin type, age, "
        "allergies, and conditions. Vague answers like 'may cause irritation' are NOT acceptable — "
        "be specific about what ingredient does, what mechanism causes the issue, and the severity. "
        "ALLERGY ALERTS are top priority — if ANY extracted ingredient matches the user's listed allergies, "
        "mark it as risk=High with a clear allergy warning."
    )

    user_message = (
        f"ANALYZE THE PRODUCT INGREDIENT LABEL IN THE ATTACHED IMAGE.\n\n"
        f"=== USER SKIN PROFILE ===\n"
        f"Age: {age_str}\n"
        f"Skin Type: {skin_type}\n"
        f"Known Allergies: {allergy_str}\n"
        f"Current Skin Conditions: {conditions_str}\n"
        f"{'Age-Specific Note: ' + age_notes if age_notes else ''}\n"
        f"{'Skin-Type Note: ' + skin_notes if skin_notes else ''}\n"
        f"{'Condition-Specific Rules: ' + cond_notes_str if cond_notes_str else ''}\n\n"
        f"=== YOUR TASKS ===\n"
        f"1. Extract EVERY ingredient visible in the image.\n"
        f"2. For EACH ingredient:\n"
        f"   - Evaluate it specifically against THIS user's age ({age_str}), skin type ({skin_type}), "
        f"allergies ({allergy_str}), and conditions ({conditions_str}).\n"
        f"   - Classify as 'harmful' or 'beneficial' for this specific user.\n"
        f"   - For harmful: assign risk 'High' (allergen match, serious comedogenic risk, age contraindication) "
        f"or 'Medium' (known irritant, moderately comedogenic) or 'Low' (minor concern).\n"
        f"   - For beneficial: assign rating 'Excellent' (directly targets this user's conditions) "
        f"or 'Good' (generally beneficial) or 'Moderate' (some benefit, minor concerns).\n"
        f"3. Calculate compatibility score 0-100 — deduct heavily for allergy matches (-30 each), "
        f"comedogenic ingredients for acne skin (-10 each), skin-type mismatches (-5 each). "
        f"Add points for beneficial targeted ingredients (+5 each).\n"
        f"4. Write a 3-4 sentence AI summary that mentions specific ingredients by name, "
        f"explains exactly what risk or benefit they pose for THIS user, and gives clear actionable advice.\n"
        f"5. Estimate Dryness, Irritation, and Pore Clogging risk (0-100) based on the full ingredient list "
        f"and this user's specific skin type and conditions.\n"
        f"6. Suggest 4 specific alternative product categories this user should look for instead.\n\n"
        f"=== CRITICAL OUTPUT FORMAT ===\n"
        f"Your ENTIRE response must be ONLY valid JSON starting with {{ and ending with }}. "
        f"No markdown, no backticks, no explanatory text. "
        f"IMPORTANT: Output 'ai_summary' as the VERY FIRST key in the JSON object. "
        f"Use this exact structure (ai_summary must come first):\n"
        f'{{'
        f'"ai_summary":"Detailed 3-4 sentence personalised advice mentioning specific ingredients by name and this user\'s specific skin profile. Explain exact risks and give actionable advice.",'
        f'"score":72,"score_label":"Moderate Match","score_summary":"One sentence summary.",'
        f'"harmful_ingredients":[{{"name":"Sodium Lauryl Sulfate","reason":"A harsh anionic surfactant that strips the skin\'s natural lipid barrier. Especially damaging for dry skin as it disrupts the acid mantle, causing tightness, flaking, and increased transepidermal water loss.","risk":"High"}}],'
        f'"beneficial_ingredients":[{{"name":"Glycerin","reason":"A powerful humectant that draws moisture from the environment into the skin. Excellent for dry skin — clinical studies show 20% glycerin improves skin hydration by up to 80% within 30 minutes.","rating":"Excellent"}}],'
        f'"potential_issues":{{"dryness":60,"irritation":45,"pore_clogging":20}},'
        f'"recommended_alternatives":["Sulfate-Free Cleanser","Ceramide Moisturiser","Fragrance-Free Toner","Gentle AHA Exfoliant"]}}'
    )

    response = None
    try:

        response = client.chat.completions.create(
            model="meta/llama-3.2-11b-vision-instruct",
            messages=[
                {"role": "system", "content": system_message},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_message},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            temperature=0.05,   # Very low temperature for factual, consistent output
            max_tokens=4096    # Increased to prevent JSON truncation (was 2500)
        )

        result_text = response.choices[0].message.content
        if not result_text:
            raise ValueError("The AI model returned an empty response.")

        result_text = result_text.strip()
        # Log raw response for debugging
        logger.info(f"[nvidia_analysis] Raw AI response (first 500 chars): {result_text[:500]}")

        # Strip markdown fences
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        final_result = None

        # Isolate JSON object
        if "{" in result_text:
            start = result_text.find("{")
            end   = result_text.rfind("}") + 1
            json_candidate = result_text[start:end]
            if json_candidate:
                try:
                    parsed = json.loads(json_candidate)
                    logger.info(f"[nvidia_analysis] JSON parsed OK. ai_summary present: {bool(parsed.get('ai_summary'))}")
                    final_result = parsed
                except json.JSONDecodeError as je:
                    # JSON was truncated/broken — try to salvage from raw text
                    logger.warning(f"[nvidia_analysis] JSON parse failed: {je}. Attempting partial recovery from raw text.")
                    logger.info(f"[nvidia_analysis] Full raw text:\n{result_text}")
                    final_result = _parse_markdown_response(result_text, user_profile)

        if final_result is None:
            # No JSON object found at all — full prose fallback
            logger.warning("[nvidia_analysis] No JSON object found. Using markdown parser fallback.")
            final_result = _parse_markdown_response(result_text, user_profile)

        # ── Guarantee ai_summary is NEVER empty ──────────────────────────────
        if not final_result.get('ai_summary'):
            logger.warning("[nvidia_analysis] ai_summary missing after parse — trying regex extraction from raw.")
            final_result['ai_summary'] = _extract_ai_summary_from_raw(result_text)

        if not final_result.get('ai_summary'):
            logger.warning("[nvidia_analysis] ai_summary still empty — making dedicated fallback API call.")
            final_result['ai_summary'] = _generate_ai_summary_fallback(
                client, user_profile, final_result, age_str, skin_type, allergy_str, conditions_str
            )

        if not final_result.get('ai_summary'):
            # Last resort: construct a meaningful summary from the data we have
            final_result['ai_summary'] = _build_summary_from_data(final_result, user_profile)

        return _apply_safety_rules(final_result, user_profile)

    except Exception as e:
        raw = response.choices[0].message.content if response else "No response received"
        logger.exception(f"[nvidia_analysis] Product analysis failed. Raw API text:\n{raw}")
        raise e


def _generate_ai_summary_fallback(
    client, user_profile: dict, analysis: dict,
    age_str: str, skin_type: str, allergy_str: str, conditions_str: str
) -> str:
    """
    Make a dedicated lightweight text-only API call to generate ai_summary
    when the main response failed to include it.
    """
    harmful_names  = ', '.join(i['name'] for i in analysis.get('harmful_ingredients', [])[:5]) or 'none detected'
    beneficial_names = ', '.join(i['name'] for i in analysis.get('beneficial_ingredients', [])[:5]) or 'none detected'
    score          = analysis.get('score', 'N/A')

    prompt = (
        f"You are a dermatologist. Write a 3-sentence personalised summary for this product analysis.\n"
        f"User: Age {age_str}, {skin_type} skin, allergies: {allergy_str}, conditions: {conditions_str}.\n"
        f"Compatibility score: {score}/100.\n"
        f"Harmful ingredients found: {harmful_names}.\n"
        f"Beneficial ingredients found: {beneficial_names}.\n"
        f"Write only the summary paragraph — no JSON, no bullet points, no preamble."
    )
    try:
        resp = client.chat.completions.create(
            model="meta/llama-3.2-11b-vision-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300
        )
        text = (resp.choices[0].message.content or '').strip()
        logger.info(f"[nvidia_analysis] Fallback ai_summary generated: {text[:100]}")
        return text
    except Exception as ex:
        logger.warning(f"[nvidia_analysis] Fallback ai_summary call failed: {ex}")
        return ''


def _build_summary_from_data(analysis: dict, user_profile: dict) -> str:
    """
    Last-resort: construct a human-readable summary from the structured data
    without any additional API calls.
    """
    score       = analysis.get('score', 0)
    label       = analysis.get('score_label', 'Analyzed')
    skin_type   = user_profile.get('skinType', 'your skin type')
    harmful     = analysis.get('harmful_ingredients', [])
    beneficial  = analysis.get('beneficial_ingredients', [])

    parts = [f"This product received a compatibility score of {score}/100 ({label}) for your {skin_type} skin."]

    if harmful:
        top = harmful[0]
        parts.append(
            f"Notable concern: {top['name']} — {top.get('reason', 'may cause irritation')} (Risk: {top.get('risk', 'Medium')})."
        )
    else:
        parts.append("No major harmful ingredients were detected for your profile.")

    if beneficial:
        top = beneficial[0]
        parts.append(
            f"A key beneficial ingredient is {top['name']}, which {top.get('reason', 'is suitable for your skin')}."
        )

    parts.append("Always patch-test new products and consult a dermatologist for personalised guidance.")
    return ' '.join(parts)
