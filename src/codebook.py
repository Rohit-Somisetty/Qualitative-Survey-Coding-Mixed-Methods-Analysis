"""Structured qualitative codebook definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Theme:
    """Represents a single qualitative theme."""

    name: str
    description: str
    keywords: List[str]
    example_quotes: List[str]


def get_codebook() -> Dict[str, Theme]:
    """Return the Step A rule-based themes."""

    return {
        "STRESS_BURNOUT": Theme(
            name="STRESS_BURNOUT",
            description="References to stress, burnout, or deteriorating mental health tied to care/work juggling.",
            keywords=["stress", "burned out", "overwhelmed", "mental health", "exhausted"],
            example_quotes=[
                "I am exhausted trying to keep up with work and caregiving, and my mental health is suffering.",
            ],
        ),
        "FOOD_INSECURITY": Theme(
            name="FOOD_INSECURITY",
            description="Households or providers describing lack of consistent access to nutritious food.",
            keywords=["food insecurity", "skip meals", "pantry", "groceries", "food budget"],
            example_quotes=["We stretch groceries thin and sometimes skip meals to pay tuition."],
        ),
        "CHILDCARE_ACCESS": Theme(
            name="CHILDCARE_ACCESS",
            description="Difficulty finding, keeping, or affording reliable childcare slots.",
            keywords=["waitlist", "no slots", "childcare access", "center closed", "after-school"],
            example_quotes=["We have been on a childcare waitlist for months since the center closed."],
        ),
        "AFFORDABILITY": Theme(
            name="AFFORDABILITY",
            description="Comments about tuition, fees, or essential costs being too high.",
            keywords=["too expensive", "tuition", "afford", "rising costs", "fees"],
            example_quotes=["Tuition is too expensive and every increase pushes us closer to debt."],
        ),
        "EMPLOYMENT_DISRUPTION": Theme(
            name="EMPLOYMENT_DISRUPTION",
            description="Work schedule disruptions or job instability tied to care responsibilities.",
            keywords=["miss work", "cut hours", "lost job", "shift", "employment"],
            example_quotes=["I miss work almost weekly because schedules fall apart when care falls through."],
        ),
        "PROVIDER_STAFF_SHORTAGE": Theme(
            name="PROVIDER_STAFF_SHORTAGE",
            description="Providers (or families describing providers) struggling to hire or retain staff.",
            keywords=["short staffed", "no subs", "can't hire", "burnout on staff", "positions open"],
            example_quotes=["We are short staffed and can't hire assistants, so classrooms merge daily."],
        ),
        "SCHEDULING_CONSTRAINTS": Theme(
            name="SCHEDULING_CONSTRAINTS",
            description="Irregular or conflicting schedules that limit access or service provision.",
            keywords=["schedule", "nights", "weekend", "split shift", "no coverage"],
            example_quotes=["My split shift schedule means there is no coverage for evenings or weekends."],
        ),
    }


__all__ = ["Theme", "get_codebook"]
