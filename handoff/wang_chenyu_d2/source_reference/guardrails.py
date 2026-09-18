"""
PE6201 · A2 scaffold — THE GUARDRAIL LAYER  (D3a)
====================================================================
Four things, and NONE of them involve a model. That is the point.

    1. STEP CAP            stop after N turns
    2. BUDGET CEILING      stop after N tokens
    3. ACTION DE-DUPLICATION   stop repeating an action already taken
    4. AUTONOMY GATE       hold the irreversible step for a human

A model cannot influence whether these fire, which is why D3(b)'s
guardrail cases run on the SCRIPTED backend. They test your code.

Problem B also checks booking preconditions before the gate and verifies that
a final `book` matches a successful gated action in the current run.

MAKE THE STOP LOUD. A cap that silently returns an empty answer is
worse than the loop it prevented: it turns a visible cost problem into
an invisible correctness problem. Every stop below records WHY.
====================================================================
"""


class GuardrailStop(Exception):
    """Raised when the code layer halts a run. Carries the reason so the
    decision record can say what stopped it and at which turn."""

    def __init__(self, reason, detail=""):
        self.reason = reason
        self.detail = detail
        super().__init__("%s: %s" % (reason, detail) if detail else reason)


class Guardrails:
    """One instance per run. Never share one between cases - a shared
    instance leaks state and D4 requires every case to start clean."""

    def __init__(self, max_turns, max_tokens, autonomy):
        if not isinstance(max_turns, int) or isinstance(max_turns, bool) \
                or max_turns < 0:
            raise ValueError("max_turns must be a non-negative integer")
        if not isinstance(max_tokens, int) or isinstance(max_tokens, bool) \
                or max_tokens < 0:
            raise ValueError("max_tokens must be a non-negative integer")
        if autonomy not in ("suggest", "confirm", "act"):
            raise ValueError(
                "autonomy must be one of: suggest, confirm, act")
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self.autonomy = autonomy
        self.seen_actions = set()     # for de-duplication
        self.fired = []               # every guardrail event, for the record

    # ---- 1 · step cap -----------------------------------------------
    def check_turns(self, turn):
        if not isinstance(turn, int) or isinstance(turn, bool) or turn < 0:
            raise ValueError("turn must be a non-negative integer")
        if turn > self.max_turns:
            self._fire("step_cap", "reached %d turns" % self.max_turns)
            raise GuardrailStop("step_cap",
                                "hit the %d-turn cap without a conclusion"
                                % self.max_turns)

    # ---- 2 · budget ceiling -----------------------------------------
    def check_budget(self, tokens_so_far):
        if not isinstance(tokens_so_far, (int, float)) \
                or isinstance(tokens_so_far, bool) or tokens_so_far < 0:
            raise ValueError("tokens_so_far must be a non-negative number")
        if tokens_so_far > self.max_tokens:
            self._fire("budget_ceiling", "%d tokens" % tokens_so_far)
            raise GuardrailStop("budget_ceiling",
                                "spent %d tokens, ceiling is %d"
                                % (tokens_so_far, self.max_tokens))

    # ---- 3 · action de-duplication ----------------------------------
    def check_duplicate(self, tool, args):
        """A loop has no memory of its own actions unless you give it one.

        This IS that memory. Class 4's loop failure was exactly this
        guard deleted: 8 turns, no answer, 1.6x the cost, and NO
        exception raised. It did not crash. It burned money in a circle.
        """
        if not isinstance(tool, str) or not tool:
            raise ValueError("tool must be a non-empty string")
        if not isinstance(args, dict):
            raise TypeError("args must be a dictionary")

        # Freeze the complete argument structure.  Sorting only the top-level
        # items is not enough: nested dictionaries can be ordered differently,
        # and callers may mutate a list/dict after the first check.
        signature = (tool, self._freeze(args))
        if signature in self.seen_actions:
            self._fire("duplicate_action", "%s repeated" % tool)
            raise GuardrailStop("duplicate_action",
                                "%s called again with identical arguments "
                                "- the loop is not progressing" % tool)
        self.seen_actions.add(signature)

    @classmethod
    def _freeze(cls, value):
        """Return a deterministic, hashable representation of action args."""
        if isinstance(value, dict):
            return ("dict", tuple(sorted(
                ((cls._freeze(key), cls._freeze(item))
                 for key, item in value.items()), key=repr)))
        if isinstance(value, (list, tuple)):
            return (type(value).__name__, tuple(cls._freeze(item)
                                                for item in value))
        if isinstance(value, set):
            return ("set", tuple(sorted((cls._freeze(item)
                                          for item in value), key=repr)))
        try:
            hash(value)
        except TypeError:
            return (type(value).__name__, repr(value))
        return (type(value).__name__, value)

    # ---- 4 · autonomy gate ------------------------------------------
    def gate(self, action_name, payload, approve=None):
        """Called ONLY in front of the irreversible step.

        Note where this sits: in front of the ACTION, not in front of the
        agent. An agent gated as a whole is not an agent, it is a form.

        `approve` is a callable the harness supplies. On the scripted
        backend it auto-approves so the run is deterministic - and the
        record still shows the gate was passed, which is what a marker
        checks for.
        """
        if not isinstance(action_name, str) or not action_name:
            raise ValueError("action_name must be a non-empty string")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dictionary")

        if self.autonomy == "act":
            self._fire("gate_passed", "%s (autonomy=act)" % action_name)
            return True
        if self.autonomy == "suggest":
            self._fire("gate_held", "%s (autonomy=suggest)" % action_name)
            return False
        # confirm
        ok = approve is not None and approve(action_name, payload) is True
        self._fire("gate_%s" % ("passed" if ok else "held"),
                   "%s (autonomy=confirm)" % action_name)
        return ok

    def check_booking_preconditions(self, case_id, payload, validator):
        """Stop an invalid proposed booking before requesting approval."""
        if payload.get("referral_id") != case_id:
            detail = "booking referral does not match the current case"
            self._fire("booking_invalid", detail)
            raise GuardrailStop("booking_invalid", detail)
        try:
            validator(**payload)
        except (TypeError, ValueError) as exc:
            detail = str(exc)
            self._fire("booking_invalid", detail)
            raise GuardrailStop("booking_invalid", detail) from exc

    @staticmethod
    def booking_confirmed(case_id, booked, tool_trace, events):
        """Whether the slot was actually booked after a gate passed."""
        fields = ("clinic", "date", "time")
        valid = isinstance(booked, dict) and all(booked.get(f) for f in fields)
        if valid:
            valid = any(
                entry.get("tool") == "book_slot"
                and entry.get("error") is None
                and isinstance(entry.get("observation"), dict)
                and entry["observation"].get("booked") is True
                and entry.get("args", {}).get("referral_id") == case_id
                and entry["observation"].get("referral_id") == case_id
                and all(entry["args"].get(f) == booked[f]
                        and entry["observation"].get(f) == booked[f]
                        for f in fields)
                for entry in tool_trace)
        return valid and any(
            event.get("guardrail") == "gate_passed" for event in events)

    def check_booking_record(self, case_id, booked, tool_trace):
        """A final `book` must match a successful, gated booking in this run."""
        if not self.booking_confirmed(case_id, booked, tool_trace, self.fired):
            detail = "final book has no matching approved book_slot result"
            self._fire("booking_unverified", detail)
            raise GuardrailStop("booking_unverified", detail)

    # ---- bookkeeping ------------------------------------------------
    def _fire(self, kind, detail):
        self.fired.append({"guardrail": kind, "detail": detail})
