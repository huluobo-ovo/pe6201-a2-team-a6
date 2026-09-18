"""
PE6201 · A2 scaffold — THE AGENT LOOP  (D1)
====================================================================
    thought -> action -> observation -> repeat -> final

That is the whole of ReAct, and it is hand-rolled here on purpose. No
framework owns your loop: when it misbehaves you need to be able to
read the twelve lines that did it.

WHAT MAKES THIS AN AGENT RATHER THAN A WORKFLOW: the number of steps is
decided by the DATA, not by you. A one-line claim with a live policy is
a short run. A four-line claim with a pre-authorisation to chase is a
long one. You did not write that branch - the record did.

--------------------------------------------------------------------
INSTRUMENTATION IS NOT OPTIONAL

Every run records turns, tokens, cost, every tool call and every
guardrail event. D6's cost model and D7's loop failure both need
numbers that were captured WHILE THE RUN HAPPENED. A team that adds
instrumentation afterwards has to run the whole battery again.

You cannot report a failure you had no way of noticing.
====================================================================
"""
import time

import config
import prompt
import tools
from backends import make_backend
from guardrails import Guardrails, GuardrailStop


def run_case(case_id, problem=None, approve=None, verbose=False,
             execution_mode="grouped"):
    """Run ONE case from a clean state and return the decision record.

    ISOLATION (D4): everything this function needs is created inside it.
    No case may depend on a previous one having run - so no module-level
    counters, no shared guardrail object, no leftover transcript.
    """
    problem = problem or config.PROBLEM
    started = time.time()

    guards = Guardrails(config.MAX_TURNS, config.MAX_TOKENS_PER_RUN,
                        config.AUTONOMY)
    # WHAT THE MODEL IS TOLD. On the scripted backend these are ignored -
    # the moves are pre-written, so no prompt is ever sent. On the live
    # backend this IS the experiment D2(b) measures: the descriptors and
    # the routing rules, assembled by prompt.build_system_prompt().
    #     python3 run_eval.py --prompt      to see the exact text
    # Pass the requested scripted mode through the backend factory.
    # The trailing optional parameter keeps existing run_case calls valid.
    backend = make_backend(
        case_id,
        tool_descriptors=prompt.descriptors_for(
            problem, config.DESCRIPTOR_VERSION),
        system_prompt=prompt.build_system_prompt(problem),
        execution_mode=execution_mode)

    transcript = []      # what the model would see
    evidence = []        # every tool actually called, in order
    # Step 1: Keep a separate execution log for each case.
    tool_trace = []

    # TURNS ARE TOOL-CALLING TURNS. The concluding move - where the agent
    # writes its decision record - is bookkeeping, not a turn. This is the
    # same convention Appendix A uses: CLM-8842 is "turns": 4 with EIGHT
    # tool calls, because the gated action is a turn like any other and
    # the write-up afterwards is not. Count them any other way and your
    # D2(c) arithmetic stops agreeing with the brief.
    turns = 0
    iterations = 0       # loop-safety only; never reported
    tokens_in = tokens_out = 0
    stopped_by = None
    backend_error = None

    # Only the scripted backend auto-approves, keeping offline evaluation
    # deterministic. A live run in confirm mode needs an explicit callback.
    if approve is None and backend.name == "scripted":
        approve = lambda action, payload: True

    try:
        while True:
            iterations += 1
            if iterations > config.MAX_TURNS + 2:
                raise GuardrailStop("step_cap", "loop did not terminate")

            # Convert live API and response failures into an auditable result.
            # Configuration errors such as a missing API key remain loud exits.
            try:
                move = backend.next_move(transcript)
            except Exception as exc:
                # A malformed model response may still have consumed tokens.
                # Consume any usage retained before response validation failed.
                ti, to = backend.token_estimate(transcript)
                tokens_in, tokens_out = tokens_in + ti, tokens_out + to
                stopped_by = getattr(exc, "reason", "backend_error")
                backend_error = {
                    "iteration": iterations,
                    "type": type(exc).__name__,
                    "message": str(exc),
                }
                record = {
                    "decision": "escalate",
                    "reason": "%s at model iteration %d: %s"
                              % (stopped_by, iterations, exc),
                }
                break
            ti, to = backend.token_estimate(transcript)
            tokens_in, tokens_out = tokens_in + ti, tokens_out + to
            guards.check_budget(tokens_in + tokens_out)

            if verbose:
                label = ("conclude" if "final" in move else "turn %d" % (turns + 1))
                print("  %-9s · %s" % (label, move.get("thought", "")[:88]))

            # ---- conclude -------------------------------------------
            if "final" in move:
                record = dict(move["final"])
                if problem == "B" and record.get("decision") == "book":
                    guards.check_booking_record(
                        case_id, record.get("booked"), tool_trace)
                break

            # ---- act: one turn may carry SEVERAL calls ---------------
            turns += 1
            guards.check_turns(turns)

            # Only calls INDEPENDENT of each other belong in one turn.
            # A dependency chain cannot be shortened by running things at
            # once - that is why Problem B saves less than Problem A.
            calls = move.get("calls") or [(move["tool"], move["args"])]
            observations = []

            for name, args in calls:
                guards.check_duplicate(name, args)

                # THE GATE goes in front of the irreversible step only.
                if name == tools.GATED_ACTION.get(problem):
                    if problem == "B":
                        guards.check_booking_preconditions(
                            case_id, args, tools.validate_booking_slot)
                    if not guards.gate(name, args, approve):
                        raise GuardrailStop(
                            "gate_held",
                            "%s awaits human approval (autonomy=%s)"
                            % (name, config.AUTONOMY))

                # Step 2: Record calls only after the pre-execution guards pass.
                # Blocked attempts remain in guardrails_fired, not tool_trace.
                trace_entry = {
                    "turn": turns,
                    "tool": name,
                    "args": args,
                    "observation": None,
                    "seconds": None,
                    "error": None,
                }
                # Step 3: Measure tool execution time with a monotonic clock.
                call_started = time.perf_counter()
                try:
                    # Step 4: Save the actual result, including valid empty results.
                    result = tools.call(problem, name, args)
                    trace_entry["observation"] = result
                except GuardrailStop as stop:
                    # Step 5: Preserve the existing outer guardrail handler.
                    trace_entry["error"] = {
                        "type": type(stop).__name__,
                        "message": stop.detail,
                    }
                    raise
                except Exception as exc:
                    # Step 6: Stop this case explicitly when a tool fails.
                    # Do not continue to a booking after an incomplete lookup.
                    trace_entry["error"] = {
                        "type": type(exc).__name__,
                        "message": str(exc),
                    }
                    stopped_by = "tool_error"
                    record = {
                        "decision": "escalate",
                        "reason": (
                            f"tool {name} failed: "
                            f"{type(exc).__name__}: {exc}"
                        ),
                    }
                    break
                finally:
                    # Step 7: Save timing and trace even when execution fails.
                    trace_entry["seconds"] = round(
                        time.perf_counter() - call_started, 6
                    )
                    tool_trace.append(trace_entry)

                evidence.append(name)
                observations.append({"tool": name, "args": args,
                                     "observation": result})
                if verbose:
                    print("       %-26s -> %s" % (name, _short(result)))

            # Step 8: Also exit the outer loop after a tool error.
            # The break above exits only the inner tool-call loop.
            if stopped_by == "tool_error":
                break

            transcript.append({"role": "assistant",
                               "content": move.get("thought", "")})
            transcript.append({"role": "user",
                               "content": repr(observations)})

    except GuardrailStop as stop:
        # A LOUD STOP. The record says what halted the run and where, so
        # this never looks like a quiet wrong answer.
        stopped_by = stop.reason
        record = {"decision": "escalate",
                  "reason": "halted by the %s guardrail - %s"
                            % (stop.reason, stop.detail)}

    cost = (tokens_in / 1e6) * config.PRICE_IN + (tokens_out / 1e6) * config.PRICE_OUT

    record.update({
        "case_id": case_id,
        "evidence": evidence,
        # Step 9: Expose the execution log to the evaluator and result output.
        "tool_trace": tool_trace,
        "turns": turns,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": round(cost, 6),
        "seconds": round(time.time() - started, 3),
        "guardrails_fired": guards.fired,
        "stopped_by": stopped_by,
        "backend_error": backend_error,
        "backend": backend.name,
        # The requested route is always available for a live run.  New runs
        # also retain the model id returned by every provider response, when
        # present.  Historical frozen artifacts remain immutable and may not
        # contain the response-side field.
        "requested_model_id": getattr(backend, "requested_model_id", None),
        "model_identity_trace": getattr(backend, "model_identity_trace", []),
        # Preserve each live response's API-reported token counts for audit.
        "model_usage": getattr(backend, "usage_trace", []),
        "model_response_trace": getattr(backend, "response_trace", []),
        "provider_reported_cost_usd": round(sum(
            entry.get("provider_cost_usd", 0.0)
            for entry in getattr(backend, "usage_trace", [])), 8),
        # Make the token source explicit so estimates are never reported as
        # measurements in the evaluation or cost analysis.
        "token_measurement": (
            "api_reported" if backend.name == "live" else "scripted_estimate"
        ),
        # Only scripted runs have a controlled grouping mode in this experiment.
        "execution_mode": (
            backend.execution_mode if backend.name == "scripted" else None
        ),
    })
    return record


def _short(value, n=64):
    s = repr(value)
    return s if len(s) <= n else s[:n - 1] + "…"
