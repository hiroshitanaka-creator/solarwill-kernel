# SolarWill Kernel — Work Log

Completed tasks only. Current status and next steps live in ROADMAP.md.

---

## 2026-03-27

**Task:** Implement Week 1 results visibility and current-truth fixtures

**Result:** Completed

**Changes:**
- Added `ROADMAP.md` — current direction, Week 1 scope, next 3 tasks
- Added `WORKLOG.md` — this file, completed-task log
- Added `reports/week1_stub_vs_gemini_latest.json` — machine-readable latest summary (updated by CI)
- Updated `.github/workflows/compare_cases.yml` — added `summarize` job that generates the latest summary JSON, logs a human-readable summary, and commits the file back to the repo after each manual run

**Evidence file:** `reports/week1_stub_vs_gemini_latest.json`

**Next implication:** Run `compare_cases` workflow manually to populate the first real result set. Review failure counts to determine Week 2 scope.

---

**Task:** Week 1 compare summary populated with real data

**Result:** Completed

**Changes:**
- Both stub and gemini runs completed 5/5 cases; failure_count = 0 for both
- Constraint distribution identical across both runs: passed 2, warn 2, blocked 1
- Stub run: all 5 cases used `backend_used=stub` as expected
- Gemini run: 4 cases used `backend_used=gemini`; 1 blocked case short-circuited before model call and returned `backend_used=stub` by design (`run_decision` in `src/solarwill/app.py`)

**Evidence file:** `reports/week1_stub_vs_gemini_latest.json`

**Next implication:** Create `docs/results/week1_compare.md` to document run results in human-readable form; define Week 2 quality-comparison criteria.
