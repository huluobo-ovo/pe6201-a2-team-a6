"""
PE6201 · A2 scaffold — THE TWO BACKENDS
====================================================================
A backend answers ONE question: given the conversation so far, what
does the agent do next?

It returns either
    {"tool": "name", "args": {...}, "thought": "..."}      -> call a tool
    {"final": {...}, "thought": "..."}                     -> conclude

EXACTLY ONE FUNCTION IN THIS WHOLE REPOSITORY KNOWS A VENDOR EXISTS.
It is `_live_call` at the bottom. That is the D5 requirement, and it is
what makes swapping models a one-string change.

--------------------------------------------------------------------
WHY THE SCRIPTED BACKEND IS NOT A TOY

It replays a fixed sequence of decisions for a known case. That makes
your whole run deterministic, free, and reproducible by a stranger -
which is what D5(a) is marked on, and what makes D3(b) and D7 cost
nothing.

It is also the honest way to test your CODE. A guardrail either fires
or it does not; a model has no say in that. Scripting the model's
moves is how you test the parts you wrote.
====================================================================
"""
import json
import urllib.error
import urllib.request
from copy import deepcopy

import config


class LiveBackendError(RuntimeError):
    """Base error carrying a stable stopped_by value for live runs."""

    reason = "backend_error"


class LiveAPIError(LiveBackendError):
    """The live provider could not return a usable HTTP response."""

    reason = "api_error"


class LiveResponseError(LiveBackendError):
    """The provider responded, but its payload or model move was invalid."""

    reason = "response_error"


# =====================================================================
# SCRIPTED
# =====================================================================
# One entry per case you have scripted. The value is the list of moves
# the "model" makes, in order.
#
# ADD YOUR OWN CASES HERE. To script a case: work out what a correct
# agent would do, step by step, and write the steps down. If you cannot
# write them down, you do not yet understand the case - which is
# useful to discover now rather than at 2am on the 13th.
SCRIPTS = {

    # ---------------------------------------------------------------
    # PROBLEM B · REF-5602 - the booking from Appendix A.
    # Six tool calls. Turns 2 and 3 each fire two calls at once, so the
    # run is FOUR turns rather than six. See D2(c) in the brief.
    # ---------------------------------------------------------------
    "REF-5602": [
        {"thought": "I have a referral id and nothing else. Fetch the record.",
         "calls": [("get_referral", {"referral_id": "REF-5602"})]},

        {"thought": "Two things I need next do not depend on each other: "
                    "the specialty's rules, and whether this patient already "
                    "has an appointment. Fire both together.",
         "calls": [("check_referral_criteria", {"specialty": "OPH",
                                                "referral_id": "REF-5602"}),
                   ("lookup_patient", {"patient_id": "P-1180"})]},

        {"thought": "No red flag, right department, VF-01 attached, no "
                    "duplicate. Band is routine, so the window runs 8 weeks "
                    "from as_of 2026-09-09, to 2026-11-04. I will query both "
                    "halves of that window at once. This is a gamble: if the "
                    "near half had a slot, the second query was wasted.",
         "calls": [("get_clinic_slots", {"specialty": "OPH", "band": "routine",
                                         "from": "2026-09-09", "to": "2026-09-30"}),
                   ("get_clinic_slots", {"specialty": "OPH", "band": "routine",
                                         "from": "2026-10-01", "to": "2026-11-04"})]},

        {"thought": "OPH-C2 is full until 14 October. First bookable slot "
                    "inside the window is 2026-10-14 11:20. Book it - this is "
                    "the irreversible step, so it goes through the gate.",
         "calls": [("book_slot", {"clinic": "OPH-C2", "date": "2026-10-14",
                                  "time": "11:20", "referral_id": "REF-5602"})]},

        {"final": {
            "decision": "book",
            "booked": {"clinic": "OPH-C2", "date": "2026-10-14", "time": "11:20"},
            "reason": "Urgency band routine, so an 8-week window from as_of "
                      "2026-09-09 closing 2026-11-04; booked at 5 weeks. "
                      "VF-01 present. No existing OPH appointment for P-1180. "
                      "OPH-C2 was full until 2026-10-14.",
         },
         "thought": "Record the band, the window, the tests and the duplicate "
                    "check - the answer key asks for all four."},
    ],

    # ---------------------------------------------------------------
    # PROBLEM A · CLM-8842 - the partly payable claim from Appendix A.
    # Three lines, one of them excluded, one needing a pre-authorisation.
    # ---------------------------------------------------------------
    "CLM-8842": [
        {"thought": "Turn 1 must run alone: everything else needs the member, "
                    "the hospital and the LINE ITEMS this returns.",
         "calls": [("get_claim", {"claim_id": "CLM-8842"})]},

        {"thought": "Now five calls that depend on nothing but that record. "
                    "The policy, the hospital, and one coverage check PER LINE "
                    "- three lines, three checks. All independent, so one turn.",
         "calls": [("lookup_policy", {"member_id": "M-2214"}),
                   ("check_coverage", {"code": "47120", "policy_id": "POL-3310"}),
                   ("check_coverage", {"code": "31255", "policy_id": "POL-3310"}),
                   ("check_coverage", {"code": "62480", "policy_id": "POL-3310"}),
                   ("lookup_hospital", {"hospital_id": "H-114"})]},

        {"thought": "This one CANNOT join the turn above: I did not know which "
                    "line needed a pre-authorisation until coverage answered. "
                    "That is the dependency rule. Only 62480 needs one.",
         "calls": [("get_preauthorisation", {"member_id": "M-2214",
                                             "procedure_code": "62480",
                                             "date_of_service": "2026-09-02"})]},

        {"thought": "A disposition for every line, then send. This is the "
                    "irreversible step, so it goes through the gate - and it "
                    "is a turn like any other.",
         "calls": [("issue_decision_letter", {
             "claim_id": "CLM-8842",
             "decision": "approve_in_principle",
             "lines_resolved": 3,
             "approved_total": 2180,
             "refused_total": 300})]},

        {"final": {
            "decision": "approve_in_principle",
            "reason": "3 lines. 47120 covered (1400). 62480 covered, PA-5521 "
                      "cited, valid on 2026-09-02 (780). 31255 refused under "
                      "EX-14 cosmetic dermatology (300). approved_total 2180, "
                      "refused_total 300. H-114 is on panel.",
         },
         "thought": "Eight calls, four turns. Not an approve and not a "
                    "decline: one decision letter covering both."},
    ],
}

# D5(a) must cover the whole submitted evaluation set, not only the one
# worked example above.  The scenario builder derives deterministic replays
# from fixture records and the fixed routing order without reading the answer
# key.  Keep the explicit worked examples when ids overlap because their exact
# grouped-call traces are also D2(c) evidence.
from evaluation_scripts import build_problem_b_scripts

for _case_id, _steps in build_problem_b_scripts().items():
    SCRIPTS.setdefault(_case_id, _steps)


def build_script_steps(case_id, execution_mode="grouped"):
    """Build an independent action sequence for one scripted run."""

    # Step 1: Reject unsupported modes instead of silently guessing.
    if execution_mode not in ("grouped", "sequential"):
        raise ValueError(
            "execution_mode must be 'grouped' or 'sequential'"
        )

    # Step 2: Copy nested arguments too, keeping the source script unchanged.
    steps = deepcopy(SCRIPTS[case_id])

    # Step 3: Preserve the original grouping for the default mode.
    if execution_mode == "grouped":
        return steps

    sequential_steps = []
    for step in steps:
        # Step 4: Keep the final answer separate from tool-calling actions.
        if "final" in step:
            sequential_steps.append(step)
            continue

        # Step 5: Accept both action formats supported by the agent loop.
        calls = step.get("calls")
        if calls is None:
            calls = [(step["tool"], step["args"])]

        # Step 6: Fail explicitly if an action contains no tool calls.
        if not calls:
            raise ValueError("A scripted action must contain a tool call")

        # Step 7: Leave existing single-call actions unchanged.
        if len(calls) == 1:
            sequential_steps.append(step)
            continue

        # Step 8: Split groups while preserving call order and arguments.
        # Neutral replay text avoids claiming that calls still run together.
        for name, args in calls:
            sequential_steps.append({
                "thought": (
                    f"Sequential replay: execute {name} "
                    "as a separate tool-calling turn."
                ),
                "calls": [(name, args)],
            })

    # Step 9: Return the derived sequence; SCRIPTS remains the shared source.
    return sequential_steps


class ScriptedBackend:
    """Replays SCRIPTS[case_id]. Deterministic, free, offline."""

    name = "scripted"

    def __init__(self, case_id, execution_mode="grouped"):
        if case_id not in SCRIPTS:
            raise SystemExit(
                "\n  No script for case %r.\n"
                "  The scripted backend replays moves you wrote down; it does\n"
                "  not invent them. Two ways forward:\n"
                "    1. add %r to SCRIPTS in backends.py, or\n"
                "    2. set BACKEND = \"live\" in config.py (this costs money).\n"
                "  Scripted cases so far: %s\n"
                % (case_id, case_id, ", ".join(sorted(SCRIPTS))))
        # Step 10: Store the mode and prepare this run's private sequence.
        # Defaulting to grouped preserves existing constructor calls.
        self.execution_mode = execution_mode
        self.steps = build_script_steps(case_id, execution_mode)
        # Start replaying at the first action in the selected sequence.
        self.i = 0

    def next_move(self, transcript):
        """`transcript` is ignored on purpose - a script does not react.
        That is what makes it reproducible."""
        if self.i >= len(self.steps):
            return {"final": {"decision": "escalate",
                              "reason": "script ended without a conclusion"},
                    "thought": "script exhausted"}
        step = self.steps[self.i]
        self.i += 1
        return step

    # Token counts on the scripted backend are ESTIMATES, so your cost
    # arithmetic has something to chew on. They are not measurements and
    # you must not report them as such - D6 wants MEASURED counts, which
    # means the live battery.
    @staticmethod
    def token_estimate(transcript):
        return 1800 + 600 * len(transcript), 120


# =====================================================================
# LIVE
# =====================================================================
class LiveBackend:
    """Real model through OpenRouter. Costs money. D5(b) only."""

    name = "live"

    def __init__(self, case_id, tool_descriptors, system_prompt):
        self.case_id = case_id
        self.tools = tool_descriptors
        self.system_prompt = system_prompt
        # Preserve both sides of model identity.  ``requested_model_id`` is
        # the exact OpenRouter route configured for the run; the response
        # trace records the provider-returned model id when the endpoint
        # supplies one.  Keeping both avoids silently treating a requested
        # alias as proof of the provider-resolved model.
        self.requested_model_id = config.MODEL
        self.model_identity_trace = []
        # Step 1: Keep the latest API-reported usage for the agent loop.
        self.last_usage = {"prompt_tokens": 0, "completion_tokens": 0,
                           "total_tokens": 0}
        self.usage_available = False
        # Step 2: Preserve per-response usage for later cost auditing.
        self.usage_trace = []
        self.response_trace = []

    def next_move(self, transcript):
        # A failed request must not reuse usage from the preceding response.
        self.usage_available = False
        # Step 3: Give the live model the case identifier on every stateless
        # request. The system prompt describes the task but not the case.
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user",
             "content": "Process case_id %s using the available tools."
                        % self.case_id},
        ]
        for entry in transcript:
            messages.append({"role": entry["role"], "content": entry["content"]})
        payload = _live_call(messages)

        # Step 4: Require measured usage instead of silently recording zeros.
        if not isinstance(payload, dict):
            raise LiveResponseError("live API response was not a JSON object")
        returned_model_id = payload.get("model")
        if not isinstance(returned_model_id, str) or not returned_model_id.strip():
            returned_model_id = None
        self.model_identity_trace.append({
            "requested_model_id": self.requested_model_id,
            "provider_returned_model_id": returned_model_id,
        })
        usage = payload.get("usage") or {}
        if "prompt_tokens" not in usage or "completion_tokens" not in usage:
            raise LiveResponseError("live API response did not include token usage")
        try:
            prompt_tokens = int(usage["prompt_tokens"])
            completion_tokens = int(usage["completion_tokens"])
            total_tokens = int(usage.get(
                "total_tokens", prompt_tokens + completion_tokens))
        except (TypeError, ValueError) as exc:
            raise LiveResponseError("live API token usage was not numeric") from exc
        if min(prompt_tokens, completion_tokens, total_tokens) < 0:
            raise LiveResponseError("live API token usage contained a negative value")
        self.last_usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }
        self.usage_available = True
        usage_entry = dict(self.last_usage)
        if isinstance(usage.get("cost"), (int, float)):
            usage_entry["provider_cost_usd"] = float(usage["cost"])
        if isinstance(usage.get("cost_details"), dict):
            usage_entry["provider_cost_details"] = usage["cost_details"]
        self.usage_trace.append(usage_entry)

        # Step 5: Parse only the assistant content after usage is recorded.
        try:
            raw = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LiveResponseError(
                "live API response did not include assistant content"
            ) from exc
        if not isinstance(raw, str) or not raw.strip():
            raise LiveResponseError("live API returned empty assistant content")
        self.response_trace.append(raw)
        return _parse_move(raw)

    def token_estimate(self, transcript):
        """Return measured usage from the most recent live API response.

        The method name is retained because the agent loop also uses it for
        scripted estimates. In live mode these values come from the API.
        """
        if not self.usage_available:
            return 0, 0
        self.usage_available = False
        return (self.last_usage["prompt_tokens"],
                self.last_usage["completion_tokens"])


def _parse_move(text):
    """The model must answer in JSON. Anything else is a run you cannot
    grade, so say so loudly rather than guessing."""
    try:
        move = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LiveResponseError("model did not return parseable JSON") from exc

    # Reject malformed moves before they reach the agent loop.
    if not isinstance(move, dict):
        raise LiveResponseError("model response JSON was not an object")
    if "final" in move:
        if not isinstance(move["final"], dict):
            raise LiveResponseError("model final response was not an object")
        return move

    calls = move.get("calls")
    if calls is None and "tool" in move and "args" in move:
        calls = [(move["tool"], move["args"])]
    if not isinstance(calls, list) or not calls:
        raise LiveResponseError("model response contained no final answer or tool calls")
    for call in calls:
        if (not isinstance(call, (list, tuple)) or len(call) != 2 or
                not isinstance(call[0], str) or not isinstance(call[1], dict)):
            raise LiveResponseError("model returned a malformed tool call")
    return move


def _live_call(messages):
    """>>> THE ONLY FUNCTION IN THIS REPOSITORY THAT KNOWS A VENDOR <<<

    Everything else speaks in terms of moves and transcripts. Swapping
    vendor means rewriting this one function, and changing MODEL and
    BASE_URL in config.py. Nothing else.
    """
    if not config.API_KEY:
        raise SystemExit(
            "\n  BACKEND is 'live' but OPENROUTER_API_KEY is not set.\n"
            "    export OPENROUTER_API_KEY='sk-or-...'\n"
            "  Or set BACKEND = 'scripted' in config.py, which is free.\n")
    body = json.dumps({
        "model": config.MODEL,
        "messages": messages,
        "temperature": 0,
        "max_tokens": config.MAX_OUTPUT_TOKENS,
    }).encode()
    req = urllib.request.Request(
        config.BASE_URL.rstrip("/") + "/chat/completions",
        data=body,
        headers={"Authorization": "Bearer " + config.API_KEY,
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            payload = json.load(r)
    except urllib.error.HTTPError as exc:
        # Report the provider status without exposing request credentials.
        raise LiveAPIError("live API returned HTTP %s" % exc.code) from exc
    except urllib.error.URLError as exc:
        raise LiveAPIError("live API network error: %s" % exc.reason) from exc
    except TimeoutError as exc:
        raise LiveAPIError("live API request timed out") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise LiveResponseError("live API returned invalid JSON") from exc
    # Return the whole response so LiveBackend can retain measured usage.
    return payload


def make_backend(case_id, tool_descriptors=None, system_prompt="",
                 execution_mode="grouped"):
    # Validate the mode before constructing a backend.
    if execution_mode not in ("grouped", "sequential"):
        raise ValueError("execution_mode must be 'grouped' or 'sequential'")
    if config.BACKEND == "scripted":
        # Forward the mode to the scripted action-sequence builder.
        return ScriptedBackend(case_id, execution_mode=execution_mode)
    if config.BACKEND == "live":
        # Splitting live model moves is not implemented by this experiment.
        # Reject this request rather than falsely reporting a sequential run.
        if execution_mode == "sequential":
            raise ValueError("sequential mode is supported only by the scripted backend")
        return LiveBackend(case_id, tool_descriptors or [], system_prompt)
    raise SystemExit("BACKEND must be 'scripted' or 'live', not %r"
                     % config.BACKEND)
