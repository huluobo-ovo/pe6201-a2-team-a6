"""
PE6201 · A2 scaffold — THE HARNESS  (D4, D5)
====================================================================
Load the answer key, run cases, grade them, report.

--------------------------------------------------------------------
THE TWO KINDS OF CHECK, AND WHY YOU NEED BOTH

A CODE CHECK compares the answer with your answer key.
    decision == expected_decision
    No model, no person, no opinion. Deterministic, free, instant.
    It is what produces the number.

A JUDGEMENT CHECK has someone read the record and decide.
    "Does the reason actually name the band and the window?"
    A PERSON can do it. A SECOND MODEL can do it. Same kind of check -
    the only difference is who grades. (This is what A1 called L1/L2.
    The names never mattered; the difference does.)

Why both: with three possible outcomes, a coin-flip scores 33% on the
code check alone. An agent can reach the right decision for the wrong
reason and the code check will not notice. `must_record` and `trigger`
are what stop a lucky run counting as a good one.

`prepare_judgement_check` below does NOT grade. It builds the queue a
human or a second model works through. Automating the judgement is
your design decision - and if you use a model, say so, because a model
grading a model is a claim that needs defending.
====================================================================
"""
import json
import os
import statistics
from collections import defaultdict

import config
import tools
from agent import run_case
from guardrails import Guardrails


# =====================================================================
# LOADING
# =====================================================================
def load_key(problem=None):
    """The answer key. YOURS, not ours, once you have extended it.

    Starts as 15 rows and grows by one per case you write. Same file
    throughout - the harness joins on case_id and does not care which
    rows we shipped and which you added.
    """
    problem = problem or config.PROBLEM
    path = os.path.join(config.data_root(),
                        "expected_outcomes_%s.json" % problem)
    with open(path, encoding="utf-8") as fh:
        rows = json.load(fh)
    return {r["case_id"]: r for r in rows}


def load_cases(problem=None):
    """Every case id in the work queue, in file order."""
    problem = problem or config.PROBLEM
    table, field = (("referrals", "referral_id") if problem == "B"
                    else ("claims", "claim_id"))
    path = os.path.join(config.data_root(), "data_%s" % problem,
                        "%s.json" % table)
    with open(path, encoding="utf-8") as fh:
        return [r[field] for r in json.load(fh)]


# =====================================================================
# THE CODE CHECK
# =====================================================================
def code_check(record, expected):
    """Deterministic comparison. Returns (passed, [reasons it failed]).

    The decision, single trigger and exact booked slot are compared. A
    booking also needs a matching successful gated action in the tool trace;
    a model's final JSON alone is not proof of execution. The wording, turn
    count and cost are not compared.
    """
    fails = []

    if record.get("decision") != expected.get("expected_decision"):
        fails.append("decision %r, expected %r"
                     % (record.get("decision"), expected.get("expected_decision")))

    # An escalation must escalate FOR THE RIGHT REASON. A run that
    # reaches the right outcome by the wrong trigger is not a pass - it
    # got there by luck and it will not get there next time.
    if expected.get("trigger"):
        if record.get("trigger") != expected["trigger"]:
            fails.append("trigger %r, expected %r"
                         % (record.get("trigger"), expected["trigger"]))

    # Requests must name the missing item exactly.  A vague request can have
    # the right decision while still failing the department protocol.
    if expected.get("missing") is not None:
        if _normalise_missing(record.get("missing")) != \
                _normalise_missing(expected["missing"]):
            fails.append("missing %r, expected %r"
                         % (record.get("missing"), expected["missing"]))

    # A booking must book the RIGHT slot. Problem B only.
    if expected.get("booked"):
        got = record.get("booked") or {}
        for field in ("clinic", "date", "time"):
            if got.get(field) != expected["booked"][field]:
                fails.append("booked.%s %r, expected %r"
                             % (field, got.get(field), expected["booked"][field]))
        if not Guardrails.booking_confirmed(
                record.get("case_id"), got, record.get("tool_trace") or [],
                record.get("guardrails_fired") or []):
            fails.append("no matching approved book_slot result in tool trace")

    # The gated action is part of correctness, not only a guardrail detail.
    # A booking must reach it exactly once and pass its gate; every negative
    # outcome must avoid it entirely.
    record_problem = ("B" if str(record.get("case_id", "")).startswith("REF-")
                      else "A")
    gated_action = tools.GATED_ACTION.get(record_problem)
    gated_calls = [entry for entry in record.get("tool_trace", [])
                   if entry.get("tool") == gated_action
                   and entry.get("error") is None]
    gate_passes = [event for event in record.get("guardrails_fired", [])
                   if event.get("guardrail") == "gate_passed"]
    expected_calls = (1 if record_problem == "A" else
                      1 if expected.get("expected_decision") == "book" else 0)
    if len(gated_calls) != expected_calls:
        fails.append("gated action %s executed %d time(s), expected %d"
                     % (gated_action, len(gated_calls), expected_calls))
    if expected_calls and len(gate_passes) != 1:
        fails.append("irreversible-action gate passed %d time(s), expected 1"
                     % len(gate_passes))

    return (not fails), fails


def _normalise_missing(value):
    """Make supported missing-item shapes comparable without fuzzy matching."""
    if isinstance(value, dict):
        parts = [value.get("name") or value.get("item"), value.get("code")]
        value = " ".join(str(part) for part in parts if part)
    elif isinstance(value, list):
        value = "; ".join(str(item) for item in value)
    if value is None:
        return None
    return " ".join(str(value).strip().lower().split())


# =====================================================================
# THE JUDGEMENT CHECK
# =====================================================================
def prepare_judgement_check(record, expected):
    """Build ONE item for a human - or a second model - to rule on.

    This deliberately does not decide anything. `must_record` items are
    written in English and a substring match would be theatre, not a
    check. Someone reads the reason and answers yes or no per item.
    """
    return {
        "case_id": record["case_id"],
        "decision": record.get("decision"),
        "reason": record.get("reason", ""),
        "must_record": expected.get("must_record", []),
        "check_type": "code_and_judgement",
        "verdict": None,          # <- a person or a second model fills this
        "graded_by": None,        # <- "person: Priya" | "model: <name>"
    }


# =====================================================================
# RUNNING THE SET
# =====================================================================
def run_set(case_ids=None, problem=None, trials_for=None, verbose=False,
            approve=None):
    """Run cases and grade them.

    `trials_for(case_id) -> int` decides how many trials each case gets.
    D4: ordinary cases get ONE trial; NEGATIVE cases get THREE, because
    negatives are the ones that flip between runs and a single trial
    cannot tell a real refusal from a lucky one.
    """
    problem = problem or config.PROBLEM
    key = load_key(problem)
    case_ids = case_ids or load_cases(problem)
    trials_for = trials_for or (lambda cid: 3 if _is_negative(key.get(cid)) else 1)

    results, judgement_queue = [], []

    for cid in case_ids:
        expected = key.get(cid)
        if expected is None:
            # check_my_data.py catches this before you get here. If you
            # are seeing it, run the checker.
            print("  SKIP %s - no label in the answer key" % cid)
            continue

        for trial in range(1, trials_for(cid) + 1):
            record = run_case(cid, problem=problem, verbose=verbose,
                              approve=approve)
            passed, fails = code_check(record, expected)
            check_type = expected.get("check_type", "code")
            if check_type not in ("code", "code_and_judgement"):
                raise ValueError("%s has unsupported check_type %r"
                                 % (cid, check_type))
            results.append({"case_id": cid, "trial": trial, "passed": passed,
                            "fails": fails, "record": record,
                            "family": expected.get("family"),
                            "negative": _is_negative(expected),
                            "check_type": check_type})
            if trial == 1 and check_type == "code_and_judgement":
                judgement_queue.append(prepare_judgement_check(record, expected))

    return results, judgement_queue


def _is_negative(expected):
    """A negative case is one whose correct outcome is anything except
    the act - so, an ask or an escalate."""
    if not expected:
        return False
    return expected.get("expected_decision") in (
        "escalate", "request_document", "request_information")


# =====================================================================
# REPORTING
# =====================================================================
def report(results):
    """The result table. EVERY pass rate is printed with its trial count,
    because a pass rate without one is not a measurement."""
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    turns = [r["record"].get("turns", 0) for r in results]
    cost = sum(r["record"].get("cost_usd", 0.0) for r in results)
    provider_cost = sum(
        r["record"].get("provider_reported_cost_usd", 0.0)
        for r in results)
    negative = [r for r in results if r.get("negative")]
    negative_passed = sum(1 for r in negative if r["passed"])
    tokens_in = sum(r["record"].get("tokens_in", 0) for r in results)
    tokens_out = sum(r["record"].get("tokens_out", 0) for r in results)
    error_trials = sum(1 for r in results
                       if r["record"].get("backend_error")
                       or r["record"].get("stopped_by") in
                       ("backend_error", "api_error", "response_error",
                        "tool_error"))
    cases = {r["case_id"] for r in results}
    negative_cases = {r["case_id"] for r in negative}
    judgement_cases = {r["case_id"] for r in results
                       if r.get("check_type") == "code_and_judgement"}

    print()
    print("=" * 68)
    print("  CODE CHECK   %d of %d trials passed   (%.1f%%)"
          % (passed, total, 100.0 * passed / total if total else 0))
    print("=" * 68)
    print("  cases               %d (%d negative)"
          % (len(cases), len(negative_cases)))
    print("  trials              %d" % total)
    print("  negative trials     %d of %d passed (%.1f%%)"
          % (negative_passed, len(negative),
             100.0 * negative_passed / len(negative) if negative else 0))
    print("  judgement queue     %d case(s) pending human/model review"
          % len(judgement_cases))
    print("  median turns        %s" % (statistics.median(turns) if turns else "-"))
    print("  worst case turns    %s" % (max(turns) if turns else "-"))
    print("  hit the step cap    %d"
          % sum(1 for r in results
                if r["record"].get("stopped_by") == "step_cap"))
    print("  tokens in / out     %d / %d" % (tokens_in, tokens_out))
    print("  error trials        %d" % error_trials)
    print("  total cost          US$%.4f   (%s backend)"
          % (cost, results[0]["record"]["backend"] if results else "-"))
    if provider_cost:
        print("  provider cost       US$%.4f   (API-reported)" % provider_cost)
    print()

    failures = [r for r in results if not r["passed"]]
    if failures:
        print("  FAILED TRIALS - each one is either a bug or a wrong label:")
        for r in failures:
            print("    %-12s trial %d  [%s]" % (r["case_id"], r["trial"],
                                                r["family"]))
            for f in r["fails"]:
                print("        %s" % f)
        print()
        print("  Before you fix the agent, ask whether the LABEL is right.")
        print("  Test: could you justify the label to someone who had never")
        print("  seen your agent's output, using only Appendix A's routing")
        print("  table? If yes, the agent is wrong. If no, the label is.")
    else:
        print("  Every trial passed the code check.")
        if judgement_cases:
            print("  Complete the judgement queue before reporting a combined")
            print("  pass rate for the %d selected prose-evidence cases."
                  % len(judgement_cases))
    print()
    return {"cases": len(cases), "negative_cases": len(negative_cases),
            "trials": total, "passed": passed,
            "pass_rate": passed / total if total else 0.0,
            "code_pass_rate": passed / total if total else 0.0,
            "negative_trials": len(negative),
            "negative_passed": negative_passed,
            "negative_code_pass_rate": (
                negative_passed / len(negative) if negative else 0.0),
            "judgement_cases": len(judgement_cases),
            "judgement_pending": len(judgement_cases),
            "median_turns": statistics.median(turns) if turns else None,
            "worst_case_turns": max(turns) if turns else None,
            "step_cap_hits": sum(
                1 for r in results
                if r["record"].get("stopped_by") == "step_cap"),
            "tokens_in": tokens_in, "tokens_out": tokens_out,
            "error_trials": error_trials, "cost_usd": cost,
            "provider_reported_cost_usd": provider_cost}


def summarise_cases(results):
    """Return the compact per-case result table required by D4."""
    grouped = defaultdict(list)
    for result in results:
        grouped[result["case_id"]].append(result)

    rows = []
    for case_id, trials in grouped.items():
        records = [trial["record"] for trial in trials]
        passed = sum(1 for trial in trials if trial["passed"])
        rows.append({
            "case_id": case_id,
            "family": trials[0].get("family"),
            "negative": trials[0].get("negative", False),
            "check_type": trials[0].get("check_type", "code"),
            "trials": len(trials),
            "code_passed": passed,
            "code_pass_rate": passed / len(trials),
            "decisions": [record.get("decision") for record in records],
            "median_turns": statistics.median(
                record.get("turns", 0) for record in records),
            "tokens_in": sum(record.get("tokens_in", 0)
                             for record in records),
            "tokens_out": sum(record.get("tokens_out", 0)
                              for record in records),
            "cost_usd": round(sum(record.get("cost_usd", 0.0)
                                  for record in records), 6),
            "provider_reported_cost_usd": round(sum(
                record.get("provider_reported_cost_usd", 0.0)
                for record in records), 8),
            "errors": sum(1 for record in records
                          if record.get("backend_error")
                          or record.get("stopped_by") in
                          ("backend_error", "api_error", "response_error",
                           "tool_error")),
        })
    return rows
