#!/usr/bin/env python3
"""Analyze a two-arm conversion-rate A/B test from a CSV file."""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass


@dataclass
class Arm:
    variant: str
    users: int
    conversions: int

    @property
    def rate(self) -> float:
        return self.conversions / self.users


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def read_arms(path: str) -> list[Arm]:
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    arms = [
        Arm(
            variant=row["variant"],
            users=int(row["users"]),
            conversions=int(row["conversions"]),
        )
        for row in rows
    ]

    if len(arms) != 2:
        raise ValueError("Expected exactly two rows: control and treatment.")
    if any(arm.users <= 0 for arm in arms):
        raise ValueError("Each arm must have at least one user.")
    if any(arm.conversions < 0 or arm.conversions > arm.users for arm in arms):
        raise ValueError("Conversions must be between 0 and users.")

    return arms


def two_proportion_z_test(control: Arm, treatment: Arm) -> tuple[float, float]:
    pooled = (control.conversions + treatment.conversions) / (control.users + treatment.users)
    standard_error = math.sqrt(pooled * (1.0 - pooled) * (1.0 / control.users + 1.0 / treatment.users))

    if standard_error == 0:
        return 0.0, 1.0

    z_score = (treatment.rate - control.rate) / standard_error
    p_value = 2.0 * (1.0 - normal_cdf(abs(z_score)))
    return z_score, p_value


def recommendation(p_value: float, absolute_lift: float, alpha: float) -> str:
    if p_value < alpha and absolute_lift > 0:
        return "Ship or ramp, assuming guardrails are clean."
    if p_value < alpha and absolute_lift < 0:
        return "Do not ship; treatment underperformed."
    return "Keep learning; result is not statistically decisive."


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", help="CSV with columns: variant, users, conversions")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance threshold")
    args = parser.parse_args()

    control, treatment = read_arms(args.csv_path)
    z_score, p_value = two_proportion_z_test(control, treatment)
    absolute_lift = treatment.rate - control.rate
    relative_lift = absolute_lift / control.rate if control.rate else float("inf")

    print(f"Control:   {control.conversions}/{control.users} = {control.rate:.2%}")
    print(f"Treatment: {treatment.conversions}/{treatment.users} = {treatment.rate:.2%}")
    print(f"Absolute lift: {absolute_lift:.2%}")
    print(f"Relative lift: {relative_lift:.2%}")
    print(f"Z-score: {z_score:.3f}")
    print(f"P-value: {p_value:.4f}")
    print(f"Decision: {recommendation(p_value, absolute_lift, args.alpha)}")


if __name__ == "__main__":
    main()

