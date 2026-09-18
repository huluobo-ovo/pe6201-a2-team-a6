# Appendix: frozen six-field tool contracts
Extracted directly from prompt.descriptors_for("B", "v2"). These are the descriptors actually assembled into the model prompt.

## as_of

**name:** as_of

**purpose:** The date every urgency window is measured FROM.

**when:** Before computing any window. Cheap - call it rather than assuming.

**args:** {}

**returns:** a date string, e.g. '2026-09-09'

**failure:** Never fails. WATCH OUT: windows are counted from THIS, not from the referral's date_received. They are equal on some referrals and not on others.

## book_slot

**name:** book_slot

**purpose:** Commit the appointment. THE IRREVERSIBLE STEP.

**when:** Last, and only when all four checks passed and a legal slot was found. Never speculatively.

**args:** {"clinic": "str, from the chosen slot", "date": "str, from the chosen slot", "time": "str, from the chosen slot", "referral_id": "str, the case id"}

**returns:** {booked: true, clinic, date, time, referral_id}

**failure:** Invalid referral or slot preconditions stop before approval: red flag, wrong specialty, missing test, future duplicate, wrong band, out-of-window or full slot. A valid booking can still be held at the autonomy gate until a human explicitly approves it.

## check_referral_criteria

**name:** check_referral_criteria

**purpose:** Run the department's protocol against the referral's free text: red flags, right department, mandatory tests, band.

**when:** Immediately after get_referral. Its answers decide whether the run continues at all.

**args:** {"specialty": "str, the code on the referral", "referral_id": "str, the case id"}

**returns:** {red_flag_term (str or None), right_department (bool), missing_tests (list), band, window_weeks}

**failure:** Returns None when the referral or specialty does not exist. IT DECIDES NOTHING - it reports five facts. Apply them in order: red flag, then wrong department, then missing test, then duplicate. STOP at the first that fires. band 'routine' is the default when no trigger phrase appears; that is normal, not a failure.

## get_clinic_slots

**name:** get_clinic_slots

**purpose:** Find appointment slots that actually exist and are free, for one specialty in one urgency band inside a date window.

**when:** AFTER all four gates pass. Never before: a red flag or missing mandatory test ends the run, so an earlier slot query is both wasted and a wrong record.

**args:** {"specialty": "str, the code from the referral, e.g. OPH", "band": "str, REQUIRED; urgent|soon|routine from check_referral_criteria, not the model's own judgement", "from/to": "ISO dates for the clinical window measured from as_of()"}

**returns:** list of {clinic, specialty, band, date, time, capacity_remaining}; only rows inside the requested band/window with capacity above zero, sorted in fixture order

**failure:** An EMPTY LIST is a valid answer meaning escalate with trigger no_slot_in_window. Never widen the window or drop the band. A capacity_remaining 0 row is full and is filtered out; it is not permission to book another band.

## get_referral

**name:** get_referral

**purpose:** Fetch the referral you have been asked to handle.

**when:** Turn 1, alone. Everything else needs what it returns, so nothing can be run alongside it.

**args:** {"referral_id": "str, the case id you were given"}

**returns:** {referral_id, patient_id, referring_clinic, specialty, date_received, clinical_summary, tests_attached, tests_attached_on (may be absent)}

**failure:** Returns None when no referral has that id. That is a broken case, not an outcome - stop and say so rather than inventing a decision.

## lookup_patient

**name:** lookup_patient

**purpose:** The patient's existing appointments and how to contact them.

**when:** Any time after get_referral. Independent of the criteria check, so the two can go in one turn.

**args:** {"patient_id": "str, from the referral"}

**returns:** {patient: {patient_id, date_of_birth, existing_appointments[]}, contact: {method, value}}

**failure:** Returns None when the patient does not exist - a broken case. An EMPTY existing_appointments list is normal and means nothing is booked, which is not the same thing.