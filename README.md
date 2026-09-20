# design-clone-ab-canary

Canonical visual-clone evaluator and gate.

The flow now uses **Orca as the default orchestration layer for non-trivial visual-clone optimization**. Orca owns isolated candidate worktrees and supervised agent races; this repository remains the authority for Control + Iris + engine-parity scoring, geometry/section regression and terminal live verification.

See:

- `AGENTS.md` — mandatory operating contract.
- `docs/orca-visual-clone.md` — Orca-integrated A/B/C candidate-race flow.
- `tools/visual_diff.py` — deterministic visual comparator.
- `tools/rank_candidates.py` — deterministic winner selection against a frozen B baseline.

A local candidate is never terminal proof. Merge the selected winner, deploy it, then rerun the live A-vs-deployed-clone gate.
