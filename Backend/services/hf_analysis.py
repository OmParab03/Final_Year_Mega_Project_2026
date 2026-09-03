# services/hf_analysis.py
# ─────────────────────────────────────────────
# Calls the two Hugging Face Spaces used for skin
# analysis and normalizes their output into a
# shape the rest of the app can store/display.
#
# Space 1 (skin type classifier) — predict(image: filepath) -> json
# Space 2 (skin condition / yolo) — predict(image: dict)     -> str
# Verified via Client(space).view_api() — see CLAUDE.md.
# ─────────────────────────────────────────────

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor

from flask import current_app
from gradio_client import Client, handle_file

# The only classes either model actually predicts (confirmed by the project owner).
_KNOWN_SKIN_TYPES = ['dry', 'oily', 'combination']
_KNOWN_CONDITIONS = ['acne', 'redness', 'pigmentation']

# Cached per-process so repeated scans don't re-open a Gradio session each time.
_clients = {}

_CONNECT_RETRIES = 3
_CONNECT_RETRY_DELAY = 3  # seconds


def _get_client(space_id: str) -> Client:
    if space_id in _clients:
        return _clients[space_id]

    last_error = None
    for attempt in range(1, _CONNECT_RETRIES + 1):
        try:
            # Passing a token (if configured) moves these calls off the shared
            # anonymous-usage quota (relevant for ZeroGPU-backed Spaces like the
            # condition detector) onto the token owner's own quota. httpx_kwargs
            # raises the default 5s connect timeout, which is too tight for a
            # slower connection completing a TLS handshake to *.hf.space.
            client = Client(
                space_id,
                token=current_app.config.get('HF_TOKEN') or None,
                httpx_kwargs={'timeout': 30.0},
            )
            _clients[space_id] = client
            return client
        except Exception as exc:  # transient network/TLS hiccups — worth a retry
            last_error = exc
            if attempt < _CONNECT_RETRIES:
                time.sleep(_CONNECT_RETRY_DELAY)

    raise last_error


def _normalize_confidence(confidence):
    """The Space reports confidence as a 0-100 percentage; normalize to 0-1."""
    if isinstance(confidence, (int, float)):
        return confidence / 100 if confidence > 1 else confidence
    return None


def _parse_skin_type(prediction):
    """Confirmed live shape: {"prediction": "Dry", "confidence": 84.49,
    "probabilities": {"Dry": 84.49, "Oily": 15.51}}. 'prediction' is already the
    argmax over the three classes, so it's used directly rather than recomputed.
    Older/alternate shapes (plain string, Gradio Label dict) are handled as a
    fallback in case the Space's output format ever changes."""
    if isinstance(prediction, dict):
        if 'prediction' in prediction:
            return str(prediction['prediction']).strip().title(), _normalize_confidence(prediction.get('confidence'))

        if 'label' in prediction:
            label = prediction['label']
            confidence = None
            confidences = prediction.get('confidences')
            if isinstance(confidences, list) and confidences:
                top = max(confidences, key=lambda c: c.get('confidence', 0))
                label = top.get('label', label)
                confidence = top.get('confidence')
            return str(label).title(), confidence

        try:
            label, confidence = max(prediction.items(), key=lambda kv: kv[1])
            return str(label).title(), float(confidence)
        except (ValueError, TypeError):
            return json.dumps(prediction), None

    if isinstance(prediction, str):
        return prediction.strip().title(), None

    if isinstance(prediction, (list, tuple)) and prediction:
        first = prediction[0]
        if isinstance(first, dict) and 'label' in first:
            return str(first['label']).title(), first.get('confidence')
        return str(first).title(), None

    return str(prediction), None


def _parse_conditions(raw_text):
    """The condition Space returns a free-form Textbox string, not guaranteed JSON,
    so this tries structured JSON first and falls back to keyword/percentage scanning."""
    text = (raw_text or '').strip()

    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        data = None

    if isinstance(data, list):
        conditions = []
        for item in data:
            if isinstance(item, dict):
                label = item.get('label') or item.get('class') or item.get('name')
                confidence = item.get('confidence', item.get('score'))
                if label:
                    conditions.append({'label': str(label).title(), 'confidence': confidence})
        return conditions

    if isinstance(data, dict):
        # Same classifier shape as the skin-type Space: {"prediction": "Acne", ...}
        if 'prediction' in data:
            label = str(data['prediction']).strip()
            if label.lower() in ('none', 'normal', 'clear', 'no condition', ''):
                return []
            return [{'label': label.title(), 'confidence': _normalize_confidence(data.get('confidence'))}]

        return [
            {'label': str(label).title(), 'confidence': confidence}
            for label, confidence in data.items()
        ]

    if not text:
        return []

    lowered = text.lower()
    if 'normal' in lowered and not any(k in lowered for k in _KNOWN_CONDITIONS):
        return []

    conditions = []
    for keyword in _KNOWN_CONDITIONS:
        if keyword in lowered:
            match = re.search(rf'{keyword}[^0-9%]{{0,15}}(\d+(?:\.\d+)?)\s*%?', lowered)
            confidence = None
            if match:
                value = float(match.group(1))
                confidence = value / 100 if value > 1 else value
            conditions.append({'label': keyword.title(), 'confidence': confidence})

    if not conditions:
        # Nothing recognized — surface the Space's raw sentence rather than dropping it
        conditions.append({'label': text, 'confidence': None})

    return conditions


def _derive_severity_and_score(conditions):
    if not conditions:
        return 'low', 92

    weights = {'acne': 18, 'pigmentation': 12, 'redness': 10}
    score = 100
    for condition in conditions:
        weight = weights.get(condition['label'].lower(), 8)
        confidence = condition.get('confidence')
        factor = confidence if isinstance(confidence, (int, float)) else 0.7
        score -= weight * max(factor, 0.4)

    score = max(5, min(100, round(score)))
    if score >= 80:
        severity = 'low'
    elif score >= 55:
        severity = 'medium'
    else:
        severity = 'high'
    return severity, score


def analyze_skin_image(image_path: str) -> dict:
    """Calls both HF Spaces once each and returns a normalized result plus the raw
    responses (kept for debugging / future use, per skin_analysis_routes)."""
    classifier_client = _get_client(current_app.config['HF_SKIN_CLASSIFIER_SPACE'])
    condition_client   = _get_client(current_app.config['HF_SKIN_CONDITION_SPACE'])

    # Run both Spaces concurrently — they're independent HTTP calls, and each one
    # may need to cold-start (free-tier Spaces sleep after inactivity), so calling
    # them sequentially would stack two cold-starts back to back.
    with ThreadPoolExecutor(max_workers=2) as pool:
        classifier_future = pool.submit(classifier_client.predict, handle_file(image_path))
        condition_future   = pool.submit(condition_client.predict, handle_file(image_path))
        classifier_raw = classifier_future.result(timeout=180)
        condition_raw   = condition_future.result(timeout=180)

    skin_type, skin_type_confidence = _parse_skin_type(classifier_raw)
    conditions = _parse_conditions(condition_raw)
    severity, score = _derive_severity_and_score(conditions)

    return {
        'skin_type':               skin_type,
        'skin_type_confidence':    skin_type_confidence,
        'conditions':              conditions,
        'severity':                severity,
        'score':                   score,
        'raw_classifier_response': classifier_raw,
        'raw_yolo_response':       condition_raw,
    }
