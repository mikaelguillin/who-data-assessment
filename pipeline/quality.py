import re
import unicodedata

UNTRUSTED_MARKERS = (
    "ignore all previous",
    "ignorez tout contexte",
    "<<system>>",
    "<</system>>",
    "[/inst]",
    "note for reviewer",
    "do not reclassify",
    "you must now respond",
    "system override",
    "this is a system override",
)

DATE_MIN_YEAR = 2020
DATE_MAX_YEAR = 2025


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    folded = unicodedata.normalize("NFKD", value)
    ascii_text = folded.encode("ascii", "ignore").decode("ascii")
    collapsed = re.sub(r"\s+", " ", ascii_text).strip().lower()
    return collapsed or None


def is_untrusted_description(value: str | None) -> bool:
    norm = normalize_text(value)
    if not norm:
        return False
    return any(marker in norm for marker in UNTRUSTED_MARKERS)


def labels_consistent(description_norm: str | None, official_label: str | None) -> bool:
    desc = normalize_text(description_norm)
    label = normalize_text(official_label)
    if not desc or not label:
        return False
    if desc == label:
        return True
    desc_tokens = {t for t in re.split(r"[^a-z0-9]+", desc) if len(t) > 3}
    label_tokens = {t for t in re.split(r"[^a-z0-9]+", label) if len(t) > 3}
    if not desc_tokens or not label_tokens:
        return False
    overlap = desc_tokens & label_tokens
    return len(overlap) >= min(2, len(label_tokens))
