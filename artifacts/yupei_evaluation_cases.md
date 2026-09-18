# Fan Yupei Evaluation Cases

These labels were written from the Problem B routing table before the scripted
agent was run. All eight are ordinary booking cases because the 15 shipped
fixtures already contain ten negatives, the top of the recommended range.

| Case | Isolated purpose | Expected result | Wrong behaviour caught | Required evidence | Check |
|---|---|---|---|---|---|
| REF-6401 | OPH urgent phrase | Book OPH-C1, 2026-09-15 09:40 | Treating an urgent referral as routine | Urgent phrase, 2-week window, VF-01, no duplicate | Code and judgement |
| REF-6402 | CARD soon phrase | Book CARD-C3, 2026-09-25 09:30 | Treating every complete referral as routine | `recurrent`, both CARD tests, no duplicate | Code |
| REF-6403 | ORT soon phrase | Book ORT-C3, 2026-09-28 15:00 | Booking a routine-band slot outside the intended band | `not responding to treatment`, XR-KNEE, no duplicate | Code |
| REF-6404 | DER has no required tests | Book DER-C2, 2026-09-24 11:00 | Inventing a mandatory test and asking unnecessarily | Empty DER test rule, `recurrent`, no duplicate | Code |
| REF-6405 | ENT two-test routine path | Book ENT-C1, 2026-10-21 13:20 | Accepting a booking without proving both tests | AUD-01, NASO-02, 8-week window, no duplicate | Code and judgement |
| REF-6406 | ORT routine path | Book ORT-C1, 2026-10-07 09:20 | Rejecting a valid department match or crossing bands | XR-KNEE, routine window, no duplicate | Code |
| REF-6407 | CARD two-test routine path | Book CARD-C2, 2026-10-21 10:00 | A lucky slot match with unsupported reasoning | Both CARD tests, 8-week window, no duplicate | Code and judgement |
| REF-6408 | DER routine path | Book DER-C1, 2026-09-30 10:40 | Inventing a missing-test rule for DER | Empty DER test rule, routine window, no duplicate | Code |

The source records live only in the `EXTRA_*` block of
`A2_reference_data/make_fixtures_B.py`. The generated `data_B` rows and the
matching entries in `expected_outcomes_B.json` travel with them.
