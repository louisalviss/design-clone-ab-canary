# Visual Clone B — canonical operating contract

This repository is the canonical evaluator/gate for Louis' visual-clone flow. Orca is the orchestration layer for non-trivial visual-clone optimization; it does not replace the evaluator.

## Roles

- A: fresh live reference URL.
- B: frozen current clone baseline.
- C/D/E/...: Orca candidate worktrees created from the same frozen B commit unless the run is explicitly an independent capability benchmark.
- Evaluator: this repository's Control + Iris + engine-parity + geometry/section regression evidence.
- Integrator: the only actor allowed to merge the winning candidate into the baseline branch.

## Mandatory flow

1. Freeze A URL, viewport and dynamic-state normalization. Default viewport is 412x915@1x.
2. Freeze B by commit SHA and record its terminal live scores before candidate work begins.
3. Run a fresh A capture. Never rank against an old A screenshot when A live is reachable.
4. For non-trivial optimization, use Orca supervised orchestration and isolated worktrees. Load the version-matched Orca orchestration skill before mutating Orca state.
5. Fan out at least two independent candidates when there is more than one plausible implementation strategy. Candidate workers may not edit the same worktree.
6. Every worker task spec must name Target, Change, Constraints, Ownership and Observable acceptance.
7. Every candidate must run the same canonical evaluator and produce a visual-gate JSON before it can be considered.
8. Rank candidates deterministically with tools/rank_candidates.py. Do not choose a winner by visual impression alone.
9. Reject a candidate when geometry fails, engine parity is invalid, Control/Iris materially regress, or a protected section regresses beyond the run's limit.
10. Merge only the selected winner. Deploy it, then rerun A-live versus the deployed winner. Local PASS is never terminal proof.
11. If the deployed live gate fails, revert/repair; do not report DONE/PASS.

## Orca policy

When Orca is available, visual-clone optimization is an Orca-supervised run by default. Resolve the active executable according to Orca's version-matched CLI skill (`ORCA_CLI_COMMAND`, `orca-dev`, Linux `orca-ide`, or `orca`) and verify it with `status --json`. Use `orca orchestration run-create` plus supervised workers rather than ad-hoc duplicate terminals. Prefer new top-level worktrees for competing candidates so they share the same frozen Git base without stacking on one another.

If the Orca runtime/CLI is not available, stop at `ORCA_BLOCKED` for the optimization stage unless the user explicitly requests a single-agent fallback. Never silently claim that Orca was used.

## Candidate acceptance

The canonical hard limits remain:

- clone_control <= 0.05
- clone_iris <= 0.05
- target_engine_parity <= 0.03
- clone_engine_parity <= 0.03
- abs(clone_control - clone_iris) <= 0.01

For an optimization race, passing the hard gate is necessary but not sufficient. A candidate must also be non-inferior to the frozen B baseline within the configured tolerance and must improve at least one primary visual score by the configured epsilon. The default primary composite is 55% Control + 45% Iris, lower is better. If two candidates are effectively tied, prefer the smaller/cleaner patch after regression review.

## Benchmark modes

Production optimization: A is the live reference, B is the frozen current clone, and C/D/E are Orca candidates seeded from B.

Capability benchmark: A is the live reference, B is the frozen current clone, and C is an independent Orca-created clone starting only from the allowed source evidence. Do not seed C with B implementation details in this mode.

## Evidence rules

Do not trust one score in isolation. Preserve Control and Iris images, their diffs, A/B engine-parity images, gate JSON, section diagnostics, commit SHA and deployed URL. A transient/blank capture is invalid evidence; retry the capture rather than accepting the resulting score.

The visual score is a gate, not the product. Always inspect the side-by-side screenshot for obvious high-salience mismatches that may be diluted by large blank areas.
