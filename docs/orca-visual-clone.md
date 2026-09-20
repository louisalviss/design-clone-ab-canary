# Orca-integrated visual clone flow

This is the permanent orchestration layer for the Visual Clone B flow.

## Architecture

- Orca owns parallel worktrees, supervised workers, task/run lifecycle and candidate isolation.
- `design-clone-ab-canary` owns visual truth: fresh A capture, Control, Iris, engine parity, geometry/section regression and terminal live verification.
- The integrator owns exactly one merge decision after deterministic ranking.

Orca must not decide a winner from prose or agent confidence. Workers create implementations; the evaluator creates evidence; `tools/rank_candidates.py` creates the first deterministic winner decision.

## Preflight

Resolve the Orca executable using the version-matched Orca CLI skill. On Linux the installed app may expose `orca-ide`; other installations may expose `orca`. Verify the runtime before starting:

```sh
<ORCA> status --json
<ORCA> skills get orchestration --full
```

If the runtime is unavailable, the optimization stage is `ORCA_BLOCKED`. Do not silently replace it with raw `git worktree` and still call the run Orca-integrated.

## Production race

Freeze the current clone baseline B at a commit SHA and record its canonical live `visual-gate.json`. Then create one supervised Orca Run whose objective names A, the frozen B SHA, viewport and baseline metrics.

Normal topology:

```text
A live reference
        |
        +--> fresh reference capture
        |
B frozen commit + baseline visual-gate.json
        |
        +--> Orca candidate C (agent/strategy 1)
        +--> Orca candidate D (agent/strategy 2)
        +--> Orca candidate E (agent/strategy 3)
                    |
                    v
          canonical evaluator for each
                    |
                    v
          rank_candidates.py
                    |
              winner only
                    |
                 merge
                    |
                 deploy
                    |
            live terminal gate
```

Use Orca supervised orchestration, not duplicate ad-hoc terminals. Current Orca's normal coordinator flow is `orchestration run-create` followed by `orchestration worker-start`; use new top-level worktrees for competing variants from the same base. The exact command contract is versioned by Orca, so load the current orchestration skill before each orchestration mutation instead of copying stale flags from this document.

Each worker gets the same immutable context plus a strategy-specific brief. The common task spec must contain:

- Target: exact section(s), files or mismatch class.
- Change: the visual outcome to improve.
- Constraints: frozen geometry, reference URL/state, protected sections, no threshold gaming.
- Ownership: this worker's isolated candidate only.
- Observable acceptance: canonical gate JSON and section diagnostics from the same evaluator.

Workers may inspect A's DOM, computed styles, fonts and assets. They may not change evaluator thresholds or manipulate captures to improve score.

## Evidence contract

Every candidate evidence directory should contain at least:

```text
visual-gate.json
control-ab.json
iris-ab.json
A-engine-parity.json
B-engine-parity.json
A-target-control.png
B-clone-control.png
A-target-iris.png
B-clone-iris.png
control-ab-diff.png
iris-ab-diff.png
```

When section diagnostics are available, retain them beside the canonical proof. Record candidate commit SHA and worktree/dispatch identity with the report.

## Deterministic selection

Rank candidates against the frozen B gate:

```sh
python3 tools/rank_candidates.py \
  --baseline B=/proof/B/visual-gate.json \
  --candidate C=/proof/C/visual-gate.json \
  --candidate D=/proof/D/visual-gate.json \
  --candidate E=/proof/E/visual-gate.json \
  --out /proof/race-result.json
```

Default optimization policy:

- canonical hard gate must pass;
- Control and Iris may not regress more than 0.001 versus B;
- at least one of Control/Iris must improve by 0.0005 or more;
- primary composite = 0.55 Control + 0.45 Iris, lower is better;
- geometry and protected-section regression remain independent vetoes;
- near ties go to the smaller/cleaner patch after regression review.

The ranking script does not override section/geometry vetoes. The integrator applies those before merging the script's proposed winner.

## Terminal acceptance

After the winning patch is merged and deployed, run the complete canonical flow again against A live and the deployed clone URL. Only this live result can close the task as PASS.

If the deploy changes dynamic behavior, a transient capture is blank, or Control/Iris engine parity becomes invalid, treat the evidence as invalid and recapture. Do not loosen thresholds to make a candidate win.

## Independent capability benchmark

For a fair B-vs-Orca cloning benchmark, freeze B and create C without seeding it with B implementation details. Give C the same allowed A evidence and evaluator. Compare B and C only after C's live deployment. This mode measures the cloning process itself; production mode measures whether Orca can optimize an existing B.
