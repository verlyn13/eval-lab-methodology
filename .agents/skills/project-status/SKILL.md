---
name: project-status
description:
  Establish current project state before planning, editing, or reporting work; reconcile status
  after a change.
---

# Project status workflow

Use this workflow at the start of a substantive task and again before handoff.

1. Read `AGENTS.md` and the status authorities it names. Treat indexes and this skill as navigation,
   not status authority.
2. Capture `git status --short --branch`, `git log --oneline -1`, and the relevant diff. Preserve
   unrelated work.
3. Separate the evidence lanes: checked-in source and docs, local Git state, live runtime,
   remote/provider state, and pending decisions. Do not infer one lane from another.
4. Compare dated claims with current evidence. Mark contradictions, missing proof, and stale
   references explicitly; use `unknown` when a lane was not checked.
5. State the intended scope and validation before editing. Keep irreversible, external, live, paid,
   publication, and secret-bearing actions behind their project gates.
6. When behavior, posture, ownership, or a public contract changes, update the repository's named
   status authority in the same change. Keep history in Git or an archive, not in `AGENTS.md`.
7. Before handoff, run `python3 scripts/check_agent_contract.py` plus the repository gate named in
   `AGENTS.md`. Report what was verified, what remains unverified, and the next concrete action.

Prefer forward migrations. Treat version pins and captured formats as compatibility baselines:
upgrade them deliberately with fixtures, tests, and status updates instead of downgrading the
workstation or preserving an obsolete dependency by default.
