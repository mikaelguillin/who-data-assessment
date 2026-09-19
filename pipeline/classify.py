import csv
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from pipeline.models import AccountMap, Classification, HarmonisedRecord, KeywordRule, QualityIssue
from pipeline.quality import is_untrusted_description, labels_consistent


@dataclass
class ClassificationDraft:
    sha_code: str | None
    srhr_code: str | None
    method: str
    confidence: str
    rationale: str
    extra_flags: list[QualityIssue]


def load_account_maps(path: Path) -> list[AccountMap]:
    maps: list[AccountMap] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            maps.append(
                AccountMap(
                    country_code=row["country_code"],
                    account_code=row["account_code"],
                    sha_code=row["sha_code"] or None,
                    srhr_code=row["srhr_code"] or None,
                    confidence=row["confidence"],
                    generic=row.get("generic", "").strip().lower() in {"1", "true", "yes"},
                    notes=row.get("notes") or None,
                )
            )
    return maps


def load_keyword_rules(path: Path) -> list[KeywordRule]:
    rules: list[KeywordRule] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rules.append(
                KeywordRule(
                    language=row["language"],
                    pattern=row["pattern"],
                    sha_code=row["sha_code"] or None,
                    srhr_code=row["srhr_code"] or None,
                    priority=int(row["priority"]),
                    notes=row.get("notes") or None,
                )
            )
    rules.sort(key=lambda item: item.priority)
    return rules


def _downgrade(confidence: str) -> str:
    order = ["high", "medium", "low", "unmapped"]
    if confidence not in order:
        return "medium"
    index = min(order.index(confidence) + 1, len(order) - 1)
    return order[index]


def _match_keyword(record: HarmonisedRecord, rules: list[KeywordRule]) -> KeywordRule | None:
    text = record.description_norm or ""
    if not text:
        return None
    for rule in rules:
        if re.search(rule.pattern, text, flags=re.IGNORECASE):
            return rule
    return None


def classify_record(
    record: HarmonisedRecord,
    account_maps: dict[tuple[str, str], AccountMap],
    rules: list[KeywordRule],
) -> ClassificationDraft:
    extra_flags: list[QualityIssue] = []
    untrusted = any(flag.flag_code == "description_untrusted" for flag in record.flags)
    if not untrusted and is_untrusted_description(record.description_raw):
        untrusted = True
        extra_flags.append(QualityIssue(flag_code="description_untrusted"))

    account_map = None
    if record.account_code:
        account_map = account_maps.get((record.country_code, record.account_code))

    consistent = labels_consistent(record.description_raw, record.official_account_label)
    missing_desc = not (record.description_raw or "").strip()

    if account_map and not account_map.generic:
        confidence = account_map.confidence
        rationale = (
            f"CoA map {record.country_code}:{record.account_code} → "
            f"SHA {account_map.sha_code or 'unmapped'}, SRHR {account_map.srhr_code or 'unmapped'}"
        )
        if account_map.notes:
            rationale = f"{rationale}. {account_map.notes}"
        if untrusted:
            confidence = _downgrade(confidence) if confidence == "high" else confidence
            rationale = (
                f"{rationale}. Free-text ignored because description is untrusted; CoA purpose used."
            )
        elif missing_desc and confidence == "high":
            confidence = "medium"
            rationale = f"{rationale}. Description missing; confidence lowered."
        elif record.official_account_label and not consistent and not missing_desc and not untrusted:
            extra_flags.append(
                QualityIssue(
                    flag_code="coa_label_mismatch",
                    detail="Description diverges from official/derived account label",
                )
            )
            rationale = f"{rationale}. Description/label mismatch noted; CoA still authoritative."
        method = "coa_map" if account_map.sha_code or account_map.srhr_code else "unmapped"
        if not account_map.sha_code:
            method = "unmapped"
            confidence = "unmapped" if confidence == "unmapped" else confidence
        return ClassificationDraft(
            sha_code=account_map.sha_code,
            srhr_code=account_map.srhr_code,
            method=method,
            confidence=confidence,
            rationale=rationale,
            extra_flags=extra_flags,
        )

    if account_map and account_map.generic and not untrusted:
        keyword = _match_keyword(record, rules)
        if keyword:
            return ClassificationDraft(
                sha_code=keyword.sha_code,
                srhr_code=keyword.srhr_code,
                method="keyword",
                confidence="low",
                rationale=(
                    f"Generic CoA {record.account_code}; keyword /{keyword.pattern}/ applied. "
                    "Needs analyst review."
                ),
                extra_flags=extra_flags,
            )

    if account_map and account_map.generic:
        rationale = (
            f"Generic CoA {record.country_code}:{record.account_code} mapped to "
            f"SHA {account_map.sha_code or 'unmapped'}, SRHR {account_map.srhr_code or 'unmapped'}"
        )
        if untrusted:
            rationale = f"{rationale}. Untrusted text ignored."
        return ClassificationDraft(
            sha_code=account_map.sha_code,
            srhr_code=account_map.srhr_code,
            method="coa_map",
            confidence=account_map.confidence,
            rationale=rationale,
            extra_flags=extra_flags,
        )

    if not untrusted:
        keyword = _match_keyword(record, rules)
        if keyword:
            return ClassificationDraft(
                sha_code=keyword.sha_code,
                srhr_code=keyword.srhr_code,
                method="keyword",
                confidence="low",
                rationale=f"No CoA map; keyword /{keyword.pattern}/ applied. Needs analyst review.",
                extra_flags=extra_flags,
            )

    return ClassificationDraft(
        sha_code=None,
        srhr_code=None,
        method="unmapped",
        confidence="unmapped",
        rationale="No reliable CoA map or trusted keyword rule.",
        extra_flags=extra_flags,
    )


def to_classification_row(expenditure_id: int, draft: ClassificationDraft) -> Classification:
    return Classification(
        expenditure_id=expenditure_id,
        sha_code=draft.sha_code,
        srhr_code=draft.srhr_code,
        method=draft.method,
        confidence=draft.confidence,
        rationale=draft.rationale,
        is_current=True,
        classified_at=datetime.now(UTC),
        classified_by="pipeline",
    )
