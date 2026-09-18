#!/usr/bin/env python3
"""Review and reproducibly integrate the final team-owned Problem B cases.

The three proposal files are preserved at repository root as the authors'
handoffs. This script selects 20 of the 24 proposals so the final evaluation
set stays within the brief's 30--50 case limit. It is idempotent: selected rows
and labels are replaced by id before being appended.
"""

import copy
import json
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
DATA_DIR = HERE / "data_B"
LABEL_PATH = HERE / "expected_outcomes_B.json"
SUMMARY_JSON = REPO_ROOT / "artifacts" / "team_case_integration_summary.json"
SUMMARY_MD = REPO_ROOT / "artifacts" / "team_case_integration_summary.md"

PROPOSAL_FILES = (
    REPO_ROOT / "evaluation_case_proposals_yang_ruijia.json",
    REPO_ROOT / "evaluation_case_proposals_wang_chenyu.json",
    REPO_ROOT / "evaluation_case_proposals_hao_qi.json",
)

# 30 existing cases + these 20 = the maximum permitted 50. REF-6207 conflicts
# with the frozen v2 descriptor's fixture-order contract. REF-6308 changes the
# earliest DER slot for existing cases. REF-6304 and REF-6306 duplicate routing
# coverage already present in the set.
SELECTED_IDS = {
    *(f"REF-610{i}" for i in range(1, 9)),
    *(f"REF-620{i}" for i in (1, 2, 3, 4, 5, 6, 8)),
    *(f"REF-630{i}" for i in (1, 2, 3, 5, 7)),
}

EXCLUDED_REASONS = {
    "REF-6207": (
        "Supplemental only: expects chronological sorting, while the frozen "
        "v2 get_clinic_slots contract explicitly returns fixture order."
    ),
    "REF-6304": (
        "Supplemental only: routing precedence between a missing test and a "
        "duplicate is already covered; omitted to stay within 50 cases."
    ),
    "REF-6306": (
        "Supplemental only: specialty-mismatch precedence is already covered; "
        "omitted to stay within 50 cases."
    ),
    "REF-6308": (
        "Supplemental only: its new earliest DER routine slot would relabel "
        "existing frozen cases rather than isolate one new behaviour."
    ),
}

TABLE_KEYS = {
    "specialties": ("code",),
    "clinic_slots": ("clinic", "date", "time"),
    "patients": ("patient_id",),
    "contacts": ("patient_id",),
    "referrals": ("referral_id",),
}

# These proposals negated exact red-flag phrases. The system deliberately uses
# literal matching, so the reviewed wording keeps the intended urgency scenario
# without embedding the exact red-flag string in a negated sentence.
REVIEWED_SUMMARIES = {
    "REF-6204": (
        "Acute onset of intermittent eyelid twitching three days ago. Vision "
        "is unchanged, with no ocular pain or new flashes."
    ),
    "REF-6205": (
        "Recurrent sinus congestion and reduced hearing over several months. "
        "The airway remains clear and the voice is unchanged."
    ),
}


def _key(table, row):
    return tuple(row[field] for field in TABLE_KEYS[table])


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path, value):
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _normalise_label(case):
    label = copy.deepcopy(case["expected_outcome"])
    decision = label["expected_decision"]
    proposed_trigger = label.pop("single_trigger", None)
    if decision == "escalate" and proposed_trigger:
        label["trigger"] = proposed_trigger
    if isinstance(label.get("missing"), list):
        label["missing"] = "; ".join(label["missing"])
    label["contributor"] = case["owner"]
    label["proposal_id"] = case["proposed_case_id"]
    return label


def _reviewed_case(case, owner):
    reviewed = copy.deepcopy(case)
    reviewed["owner"] = owner
    case_id = reviewed["proposed_case_id"]
    if case_id in REVIEWED_SUMMARIES:
        referrals = reviewed["fixture_changes"]["referrals"]
        if len(referrals) != 1 or referrals[0]["referral_id"] != case_id:
            raise ValueError(f"{case_id}: reviewed summary target is ambiguous")
        referrals[0]["clinical_summary"] = REVIEWED_SUMMARIES[case_id]
    return reviewed


def integrate():
    proposals = []
    all_ids = set()
    for path in PROPOSAL_FILES:
        payload = _load(path)
        owner = payload["owner"]
        for case in payload["cases"]:
            reviewed = _reviewed_case(case, owner)
            case_id = reviewed["proposed_case_id"]
            if case_id in all_ids:
                raise ValueError(f"duplicate proposal id: {case_id}")
            all_ids.add(case_id)
            proposals.append(reviewed)

    expected_inventory = SELECTED_IDS | set(EXCLUDED_REASONS)
    if all_ids != expected_inventory:
        missing = sorted(expected_inventory - all_ids)
        unexpected = sorted(all_ids - expected_inventory)
        raise ValueError(
            f"proposal inventory changed; missing={missing}, unexpected={unexpected}"
        )

    selected = [case for case in proposals
                if case["proposed_case_id"] in SELECTED_IDS]
    if len(selected) != 20:
        raise ValueError(f"expected 20 selected cases, found {len(selected)}")

    changes = {table: [] for table in TABLE_KEYS}
    for case in selected:
        for table, rows in case.get("fixture_changes", {}).items():
            if table not in changes:
                raise ValueError(f"unsupported fixture table: {table}")
            changes[table].extend(copy.deepcopy(rows))

    for table, incoming in changes.items():
        path = DATA_DIR / f"{table}.json"
        current = _load(path)
        incoming_keys = [_key(table, row) for row in incoming]
        if len(incoming_keys) != len(set(incoming_keys)):
            raise ValueError(f"selected proposals duplicate a {table} key")
        selected_keys = set(incoming_keys)
        retained = [row for row in current if _key(table, row) not in selected_keys]
        _write(path, retained + incoming)

    labels = _load(LABEL_PATH)
    labels = [row for row in labels if row.get("case_id") not in SELECTED_IDS]
    labels.extend(_normalise_label(case) for case in selected)
    if not 30 <= len(labels) <= 50:
        raise ValueError(f"final evaluation set has {len(labels)} cases")
    _write(LABEL_PATH, labels)

    counts = Counter(case["owner"] for case in selected)
    negative = sum(case["expected_outcome"]["expected_decision"] != "book"
                   for case in selected)
    summary = {
        "schema_version": "1.0",
        "final_case_count": len(labels),
        "selected_team_case_count": len(selected),
        "selected_negative_case_count": negative,
        "selected_by_owner": dict(sorted(counts.items())),
        "selected_ids": sorted(SELECTED_IDS),
        "supplemental_not_executed": EXCLUDED_REASONS,
        "reviewed_text_adjustments": REVIEWED_SUMMARIES,
    }
    _write(SUMMARY_JSON, summary)

    lines = [
        "# Team evaluation case integration",
        "",
        f"The final Problem B set contains **{len(labels)} cases**. "
        f"This integrates {len(selected)} reviewed team proposals while staying "
        "inside the assignment's 30--50 case limit.",
        "",
        "## Selected cases",
        "",
    ]
    for owner, count in sorted(counts.items()):
        ids = sorted(case["proposed_case_id"] for case in selected
                     if case["owner"] == owner)
        lines.append(f"- {owner}: {count} ({', '.join(ids)})")
    lines += ["", "## Supplemental proposals not executed", ""]
    for case_id, reason in EXCLUDED_REASONS.items():
        lines.append(f"- `{case_id}` — {reason}")
    lines += [
        "",
        "The proposal source files remain unchanged for attribution. Two negated "
        "red-flag sentences were reviewed into equivalent non-triggering wording; "
        "the exact adjustments are recorded in the JSON summary.",
        "",
    ]
    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = integrate()
    print(
        "Integrated %d team cases; final set: %d"
        % (result["selected_team_case_count"], result["final_case_count"])
    )
