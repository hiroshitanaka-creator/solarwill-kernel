# SolarWill Kernel — Roadmap

## Project Goal

SolarWill Kernel is a minimal research kernel for traceable decision support. The goal is to validate that structured constraint-aware outputs (blocked / warn / passed) combined with audit-trail traces produce more auditable responses than single-answer systems. This is a research baseline, not a production system.

## Main Question

Can SolarWill provide decision support with traceable reasons and constraint enforcement, in a way that is auditable and structurally consistent across backends?

## Week 1 Scope

- Single backend at a time (stub or gemini)
- Single constraint rule (keyword-based blocked / warn / passed)
- Single trace schema (backend_requested, backend_used, constraint_result, timestamp)
- Single output contract (options, recommendation, reasons, risks, next_questions)
- Single CLI entry point (`solarwill run`)
- Fixed case set (`tests/fixtures/sample_cases.json`, v0.1, 5 cases)

## Current Status

Week 1 baseline is implemented. Stub and Gemini backends run against the fixed case set via `compare_cases.yml` (workflow_dispatch). Results are summarized in `reports/week1_stub_vs_gemini_latest.json`, which is updated automatically on each workflow run.

## Next 3 Tasks

1. **Run compare_cases workflow manually** — confirm stub and gemini both pass all 5 cases, verify `reports/week1_stub_vs_gemini_latest.json` is updated in repo.
2. **Review Week 1 results** — check failure counts and constraint accuracy from the summary file.
3. **Define Week 2 scope** — based on Week 1 results, decide what to fix or extend (constraint coverage, case set expansion, or output quality).

## Non-Goals

- Ollama improvement or local model integration
- REST API server
- UI / result viewer
- Benchmark expansion beyond the fixed case set
- Multi-agent architecture
- Full repo refactor
- Production deployment
