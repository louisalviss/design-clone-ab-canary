#!/usr/bin/env python3
"""Build the canonical Iris visual gate from four visual-diff result files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _score(path: Path) -> float:
    return float(json.loads(path.read_text(encoding="utf-8"))["score"])


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--control", type=Path, required=True)
    p.add_argument("--iris", type=Path, required=True)
    p.add_argument("--target-parity", type=Path, required=True)
    p.add_argument("--clone-parity", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--clone-limit", type=float, default=0.05)
    p.add_argument("--parity-limit", type=float, default=0.03)
    p.add_argument("--drift-limit", type=float, default=0.01)
    p.add_argument("--enforce", action="store_true")
    args = p.parse_args()

    values = {
        "clone_control": _score(args.control),
        "clone_iris": _score(args.iris),
        "target_engine_parity": _score(args.target_parity),
        "clone_engine_parity": _score(args.clone_parity),
    }
    limits = {
        "clone_control": args.clone_limit,
        "clone_iris": args.clone_limit,
        "target_engine_parity": args.parity_limit,
        "clone_engine_parity": args.parity_limit,
    }
    failures = [
        f"{key}={values[key]:.6f}>{limits[key]:.6f}"
        for key in values
        if values[key] > limits[key]
    ]
    drift = abs(values["clone_control"] - values["clone_iris"])
    if drift > args.drift_limit:
        failures.append(f"engine_score_drift={drift:.6f}>{args.drift_limit:.6f}")

    gate = {
        "schema": "iris-visual-gate-v1",
        "values": values,
        "limits": limits,
        "engine_score_drift": round(drift, 6),
        "pass": not failures,
        "failures": failures,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.out.with_suffix(args.out.suffix + ".tmp")
    tmp.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(args.out)
    print(json.dumps(gate, indent=2, sort_keys=True))
    return 1 if args.enforce and failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
