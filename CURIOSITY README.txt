CURIOSITY README (Claude's synthesis)
A research pipeline run by Claude Code. One question per project, answered in about an afternoon with DuckDB SQL plus Python, and delivered as one Excel report. Nothing is guessed: definitions and assumptions are agreed with the human BEFORE any analysis, and every number is verified independently BEFORE the human sees it.

=====================================================================
THE PRINCIPLES BEHIND IT ALL
=====================================================================
 - Agree before you compute: definitions, assumptions and the answer's format are fixed and human-approved first.
 - Checks before code, and never weakened afterwards.
 - Whoever builds it does not judge it: the Verifier recomputes independently, by a different method.
 - Everything is rebuildable: python run.py --fresh regenerates all results from data/raw/.
 - Small steps, deterministic numbers, a traceable chain from raw data to every figure in the report.


PRESENTING THE TEAM
The main Claude Code session is the ORCHESTRATOR. It runs the interview, calls the subagents in order, enforces the gates and talks to the human. It never writes analysis code and never quotes a number that is not in a verified evidence pack. Subagents cannot talk to the human or to each other; everything flows through the orchestrator.

| ROLE         | HOW IT RUNS                          | MODEL         | PHASE   | WRITES                                                              |
| Interviewer  | /interview <question> (main session) | Sonnet        | PHASE 1 | brief/research_brief.md                                             |
| Planner      | subagent "planner"                   | Opus          | PHASE 1 | data/raw/, plan/data_feasibility.md, plan/plan.md, sql/00_*         |
| Executor     | subagent "executor"                  | Sonnet / Opus | PHASE 2 | sql/, py/, checks/check_stepNN.py, run.py, evidence/                |
| Executor     | or "executor-opus" (Opus)            |               | PHASE 2 | sql/, py/, checks/check_stepNN.py, run.py, evidence/                |
| Verifier     | subagent "verifier"                  | Opus          | PHASE 2 | verify/, and the top section of evidence/stepNN.md                  |

Separation of powers: the Interviewer never touches data, the Planner never runs the analysis, the Executor never judges its own work, and the Verifier never fixes the Executor's code.


=====================================================================
PHASE 1: KNOW EXACTLY WHAT WE ARE ANSWERING
=====================================================================

1a) INTERVIEWER (Sonnet) turns a vague question into a testable research brief
- Every metric gets an operational definition a stranger could compute: numerator, denominator, filters, time grain, edge cases (nulls, ties, cancellations).
- Every assumption is tagged [STATED] (human said it) or [INFERRED] (interviewer proposed it and the human accepted it). Nothing is written that the human hasn't seen.
- Pre-registered hypotheses, useful for verifier's smell tests.
- Asks about data only once, as a hint. Does NOT verify availability (that is the Planner's job).

Fixed format of research_brief.md
 1. Question (one sentence)
 2. Definitions (table: term, operational definition, edge cases, source STATED/INFERRED)
 3. Scope (population, time window, geography/segments, explicitly out of scope)
 4. Hypotheses and pre-registered expectations
 5. Assumptions ([STATED] / [INFERRED])
 6. Format of the final answer (MANDATORY): headline sentence as fill-in-the-blank, the 1-3 tables/charts of the Excel report (sheet, rows, columns, units), required precision
 7. Data hints (unverified)
 8. Open questions / risks

1b) PLANNER (Opus) checks the data really exists, then writes the plan
Part A, Data feasibility (stop if it fails):
 1. Find candidate sources, preferring official/open ones with a clear licence.
 2. Actually download into data/raw/ (no login, ~2 GB max); record URL, date, size, SHA-256 and licence in SOURCES.md.
 3. Load into DuckDB (raw_ tables, via sql/00_load_raw.sql registered as step 0 in run.py) and profile: row counts, columns/types, null rates, min/max, candidate key uniqueness.
 4. Coverage table: for every definition (brief section 2) and every element of the answer format (section 6), name the exact table and columns that compute it, or mark NOT COVERED.
 5. Verdict: GO / GO WITH CHANGES (each change becomes a decision for the human) / NO-GO (explain, propose the closest answerable question, write no plan).
Part B, The plan (plan.md): decisions for the human (each with a recommendation), then numbered steps, then risks.
Each step states: goal, inputs, outputs, executor model (sonnet or opus + reason), acceptance checks, time estimate (<= 45 min).
Planning rules:
 - Small steps (usually 4-8) to prevent drift and keep human review feasible; if a goal needs "and" to be explained in its title, split it.
 - Step 1 is ALWAYS data cleaning + a data quality log. The last step by default builds the Excel report from a script.
 - Every number in the final answer traces back to a step (a mapping is listed at the end of the plan).
 - Acceptance checks (invariants, expected ranges, reconciliations) are written NOW, in the plan, specific enough that pass/fail can't be argued.
 - Total estimate must be <= 4 hours, otherwise cut scope and record it as a decision.

GATE 1: the human approves the plan and answers every decision. Recorded at the top of plan.md. No work starts before this.


=====================================================================
PHASE 2: EXECUTE AND VERIFY, ONE STEP AT A TIME
=====================================================================
For each step N, in order: Executor -> Verifier -> verdict. Step N+1 never starts until step N is PASS or PASS WITH NOTES.

2a) EXECUTOR (Sonnet or Opus, per the step's tag) does exactly ONE step, in this order:
 1. Write the checks first (using the shared helpers in checks/_lib.py, so every check prints PASS/FAIL with actual vs expected and the script exits non-zero on any failure) and run them once: they must fail, proving they can fail.
 2. Write the code in small pieces (sql/NN_*.sql, py/NN_*.py), running each piece before writing the next.
 3. Register the step in run.py, the single pipeline runner.
 4. Rebuild from scratch (python run.py --fresh --through NN) and run the checks until all pass.
 5. Write its half of the evidence pack (evidence/stepNN.md): what was done, files, row flow, check output, 3-5 spot-check cases, deviations.
 Returns one line only: DONE, BLOCKED: <reason>, or CHECK DISPUTED: <check>.

HARD RULES:
 - NEVER edit, loosen or delete a check to pass. If a check seems wrong, leave it failing and return CHECK DISPUTED.
 - NEVER change a definition. If the data forces a deviation (e.g. a column is 30% null), stop with BLOCKED and give options.
 - One source of truth: all logic in sql/ and py/; no hand-typed numbers anywhere; Excel only written by a script (values, not formulas, plus a Checks sheet), and only in the final step.
 - Idempotent: CREATE OR REPLACE, no timestamps in data, fixed random seeds.
 - Don't modify earlier steps' files; if unavoidable, record it in the evidence pack.
 - Document as you go: header comments in every file, every data issue in evidence/data_quality_log.md.
 - Portable: pathlib, relative paths, only duckdb / pandas / openpyxl (plus what the plan names).

2b) VERIFIER (Opus, fresh context, sees only files, never the Executor's reasoning) tries to BREAK the step, not confirm it. It never edits Executor files. Levels, in order:
 V1 Reproduce: rebuild from zero twice, compare fingerprints (row count + order-independent hash sum); rerun ALL earlier steps' checks (regression).
 V2 Audit the checks: every planned check present and not weakened; pasted output matches a real run.
 V3 Recompute blind: BEFORE reading the code, recompute the step's 1-3 headline numbers by a different method (other tool, from raw_ tables, different path). Counts must match exactly; sums/rates within 1e-9. Disagreements are reconciled down to the record.
 V4 Review the code against the definitions: join fan-out, silent drops, NULL handling, date boundaries, integer division, wrong denominators, double counting, filter order; plus documentation is true and nothing is hand-typed.
 V5 Smell tests: magnitudes, signs, distribution shape vs the plan's ranges and the human's pre-registered expectations. A contradiction is not a failure; it is tagged SURPRISE.
 V6 Sensitivity: for each threshold/modelling choice, rerun with reasonable alternatives; if the conclusion flips, tag FRAGILE.
 V7 Trace spot-checks: the Executor's cases plus 2 of its own (random with a fixed seed).
 Final-report step only, extra levels:
 1. Read back the Excel with openpyxl and compare every numeric cell to its source query; check sheets/columns/units/precision vs brief section 6.
 2. Trace every number in the headline sentence to a verified step.
 3. Rebuild everything (run.py --fresh), regenerate the workbook, run every check.

 Verdicts:
 - PASS: every level clean. Orchestrator posts one line and continues automatically.
 - PASS WITH NOTES: no errors but SURPRISE / FRAGILE / minor doc issues; work continues, notes are collected for the final review.
 - FAIL: any reproducibility, check, recomputation or definition error. Findings are listed (file:line, problem, evidence, expected behaviour) but the fix is NOT written by the Verifier.
 The verdict and a one-page human summary go at the TOP of evidence/stepNN.md.

Failure handling
 - BLOCKED or CHECK DISPUTED: the orchestrator stops and asks the human.
 - FAIL: the same executor is re-run on "fix only the Verifier's findings", then re-verified; up to 2 retries (3 attempts total). Still failing: escalate to the human with the findings and attempt history.
 - Each verified step is committed to git so the Verifier can diff exactly what a retry changed.

Closing the project (after the last step passes)
 - The orchestrator writes report/final_review.md: headline answer with verified numbers, recap of definitions/assumptions/decisions, every SURPRISE and FRAGILE note, 5 spot-check cases for the human (~10 minutes to trace), and links to the workbook, evidence packs and data quality log.
 - GATE 2: the human approves the final report. Until then the project is not done.





