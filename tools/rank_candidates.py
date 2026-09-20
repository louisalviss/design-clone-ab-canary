#!/usr/bin/env python3
"""Deterministically rank Orca visual-clone candidates against a frozen baseline.

Expected input is the canonical `iris-visual-gate-v1` JSON written by the
visual-clone evaluator. Lower visual scores are better.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


PRIMARY_KEYS = ("clone_control", "clone_iris")
PARITY_KEYS = ("target_engine_parity", "clone_engine_parity")


@dataclass
class Gate:
    name: str
    path: str
    control: float
    iris: float
    target_parity: float
    clone_parity: float
    drift: float
    hard_pass: bool
    failures: list[str]

    @property
    def composite(self) -> float:
        return 0.55 * self.control + 0.45 * self.iris


def _load(name: str, path: Path) -> Gate:
    raw = json.loads(path.read_text(encoding="utf-8"))
    values = raw.get("values") or {}
    missing = [k for k in (*PRIMARY_KEYS, *PARITY_KEYS) if k not in values]
    if missing:
        raise ValueError(f"{path}: missing values: {', '.join(missing)}")
    drift = raw.get("engine_score_drift")
    if drift is None:
        drift = abs(float(values["clone_control"]) - float(values["clone_iris"]))
    return Gate(
        name=name,
        path=str(path),
        control=float(values["clone_control"]),
        iris=float(values["clone_iris"]),
        target_parity=float(values["target_engine_parity"]),
        clone_parity=float(values["clone_engine_parity"]),
        drift=float(drift),
        hard_pass=bool(raw.get("pass", False)),
        failures=list(raw.get("failures") or []),
    )


def _named_path(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("expected NAME=PATH")
    name, path = value.split("=", 1)
    if not name or not path:
        raise argparse.ArgumentTypeError("expected NAME=PATH")
    return name, Path(path)


def _eligible(candidate: Gate, baseline: Gate, tolerance: float, epsilon: float) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not candidate.hard_pass:
        reasons.append("canonical_gate_failed")
    if candidate.control > baseline.control + tolerance:
        reasons.append(
            f"control_regression={candidate.control - baseline.control:+.6f}>tolerance={tolerance:.6f}"
        )
    if candidate.iris > baseline.iris + tolerance:
        reasons.append(
            f"iris_regression={candidate.iris - baseline.iris:+.6f}>tolerance={tolerance:.6f}"
        )
    improved = (
        candidate.control <= baseline.control - epsilon
        or candidate.iris <= baseline.iris - epsilon
    )
    if not improved:
        reasons.append(f"no_primary_improvement>=epsilon={epsilon:.6f}")
    return not reasons, reasons


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, type=_named_path, metavar="NAME=PATH")
    parser.add_argument("--candidate", action="append", required=True, type=_named_path, metavar="NAME=PATH")
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.001,
        help="maximum allowed regression on either primary score (default: 0.001)",
    )
    parser.add_argument(
        "--epsilon",
        type=float,
        default=0.0005,
        help="minimum improvement required on Control or Iris (default: 0.0005)",
    )
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(list(argv) if argv is not None else None)

    baseline = _load(args.baseline[0], args.baseline[1])
    candidates = [_load(name, path) for name, path in args.candidate]

    rows = []
    eligible = []
    for cand in candidates:
        ok, reasons = _eligible(cand, baseline, args.tolerance, args.epsilon)
        row = {
            **asdict(cand),
            "composite": round(cand.composite, 9),
            "delta_control": round(cand.control - baseline.control, 9),
            "delta_iris": round(cand.iris - baseline.iris, 9),
            "delta_composite": round(cand.composite - baseline.composite, 9),
            "eligible": ok,
            "rejection_reasons": reasons,
        }
        rows.append(row)
        if ok:
            eligible.append(cand)

    winner = min(eligible, key=lambda g: (g.composite, g.control, g.iris, g.name)) if eligible else None
    result = {
        "schema": "orca-visual-clone-race-v1",
        "baseline": {
            **asdict(baseline),
            "composite": round(baseline.composite, 9),
        },
        "policy": {
            "control_weight": 0.55,
            "iris_weight": 0.45,
            "primary_regression_tolerance": args.tolerance,
            "minimum_primary_improvement": args.epsilon,
        },
        "candidates": rows,
        "winner": winner.name if winner else None,
        "pass": winner is not None,
    }

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        tmp = args.out.with_suffix(args.out.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(args.out)
    print(text, end="")
    return 0 if winner else 2


if __name__ == "__main__":
    raise SystemExit(main())
