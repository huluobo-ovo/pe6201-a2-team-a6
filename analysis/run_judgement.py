#!/usr/bin/env python3
"""Grade selected prose-evidence cases with a named different-family model.

Raw evaluation results are never modified. Verdicts and API measurements are
written to a separate auditable sidecar.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_INPUTS = [
    "artifacts/results.json",
    "artifacts/live_results/fan_yupei_openai_gpt-5.4_v1.json",
    "artifacts/live_results/fan_yupei_openai_gpt-5.4_v2.json",
]


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _decode_json_object(text):
    candidate = text.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        candidate = "\n".join(lines).strip()
    value = json.loads(candidate)
    if not isinstance(value, dict):
        raise ValueError("judge response is not one JSON object")
    return value


def _validate_verdict(value, queue_item, model, prompt_sha):
    if value.get("case_id") != queue_item["case_id"]:
        raise ValueError("judge returned the wrong case_id")
    expected = queue_item["must_record"]
    item_verdicts = value.get("item_verdicts")
    if not isinstance(item_verdicts, list):
        raise ValueError("item_verdicts is not a list")
    criteria = [item.get("criterion") for item in item_verdicts]
    if criteria != expected:
        raise ValueError("judge criteria do not exactly match must_record")
    if any(not isinstance(item.get("met"), bool) for item in item_verdicts):
        raise ValueError("every item verdict needs a boolean met field")
    if any(not isinstance(item.get("reason"), str) or not item["reason"].strip()
           for item in item_verdicts):
        raise ValueError("every item verdict needs a non-empty reason")
    expected_overall = all(item["met"] for item in item_verdicts)
    if value.get("verdict") is not expected_overall:
        raise ValueError("overall verdict does not equal all item verdicts")
    if value.get("graded_by") != "model: " + model:
        raise ValueError("graded_by does not name the configured judge")
    if value.get("judge_prompt_sha256") != prompt_sha:
        raise ValueError("judge prompt hash mismatch")
    return value


def _content(message):
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content
                       if isinstance(part, dict))
    return str(content)


def _judge(api_key, model, rubric, prompt_sha, queue_item):
    record = {
        "case_id": queue_item["case_id"],
        "decision": queue_item.get("decision"),
        "reason": queue_item.get("reason"),
        "must_record": queue_item["must_record"],
    }
    request_body = {
        "model": model,
        "temperature": 0,
        "max_tokens": 800,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": rubric + (
                    "\nReturn exactly one JSON object. Copy every criterion "
                    "verbatim and in order. Set graded_by to 'model: %s' and "
                    "judge_prompt_sha256 to '%s'." % (model, prompt_sha)),
            },
            {
                "role": "user",
                "content": json.dumps(record, ensure_ascii=False),
            },
        ],
    }
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError("judge HTTP %s: %s" % (exc.code, detail)) from exc
    raw = _content(payload["choices"][0]["message"])
    verdict = _validate_verdict(
        _decode_json_object(raw), queue_item, model, prompt_sha)
    usage = payload.get("usage") or {}
    return {
        **verdict,
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "provider_cost_usd": usage.get("cost"),
        },
        "raw_response": raw,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", dest="inputs")
    parser.add_argument("--model", default="google/gemini-2.5-flash-lite")
    parser.add_argument("--rubric", default="artifacts/JUDGEMENT_RUBRIC.md")
    parser.add_argument("--output", default="artifacts/judgement_results.json")
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY is required for judgement runs")
    rubric_path = ROOT / args.rubric
    rubric = rubric_path.read_text(encoding="utf-8")
    prompt_sha = _sha256(rubric_path)
    source_paths = [ROOT / item for item in (args.inputs or DEFAULT_INPUTS)]
    results = []
    for path in source_paths:
        source = _load(path)
        source_rows = []
        for item in source.get("judgement_queue", []):
            source_rows.append(_judge(
                api_key, args.model, rubric, prompt_sha, item))
        results.append({
            "source_file": str(path.relative_to(ROOT)),
            "source_file_sha256": _sha256(path),
            "source_backend": source.get("run", {}).get("backend"),
            "source_model": source.get("run", {}).get("model_id"),
            "descriptor_version":
                source.get("run", {}).get("descriptor_version"),
            "freeze_sha": source.get("run", {}).get("freeze_commit_sha"),
            "judgements": source_rows,
            "passed": sum(row["verdict"] for row in source_rows),
            "total": len(source_rows),
        })
    payload = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "judge_model": args.model,
        "judge_model_family": args.model.split("/", 1)[0],
        "judge_prompt_file": str(rubric_path.relative_to(ROOT)),
        "judge_prompt_sha256": prompt_sha,
        "token_measurement": "api_reported",
        "results": results,
    }
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print("Wrote %s" % output)
    for result in results:
        print("%s: %d/%d judgement pass" % (
            result["source_file"], result["passed"], result["total"]))


if __name__ == "__main__":
    main()
