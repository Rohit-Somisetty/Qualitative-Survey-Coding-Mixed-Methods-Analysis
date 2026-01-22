"""Synthetic qualitative survey data generator for Step A."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

FRAMES = ["household", "provider"]
FRAME_WEIGHTS = [0.65, 0.35]
MONTHS = ["January 2024", "February 2024", "March 2024"]
STATES = [
    "AL",
    "AZ",
    "CA",
    "CO",
    "CT",
    "FL",
    "GA",
    "IL",
    "MA",
    "MI",
    "NC",
    "NJ",
    "NY",
    "OH",
    "PA",
    "TX",
    "WA",
]
HOUSEHOLD_INCOME = ["<30k", "30-60k", "60-100k", ">100k"]
HOUSEHOLD_INCOME_WEIGHTS = [0.25, 0.35, 0.25, 0.15]
PROVIDER_SETTINGS = ["center", "family_home", "informal", "after_school"]
PROVIDER_SETTING_WEIGHTS = [0.45, 0.25, 0.15, 0.15]

THEME_SNIPPETS: Dict[str, Dict[str, List[str]]] = {
    "STRESS_BURNOUT": {
        "household": [
            "The stress of juggling work and caregiving is overwhelming and my mental health keeps slipping.",
            "I feel burned out every week trying to cover shifts and still be a present parent.",
            "My partner and I are exhausted, constantly anxious about childcare collapsing at the last minute.",
        ],
        "provider": [
            "Staff and I are emotionally drained; burnout is spreading across the team.",
            "Managing constant schedule changes with too few people is crushing my mental health.",
            "I am overwhelmed balancing paperwork, families, and the classroom without relief.",
        ],
    },
    "FOOD_INSECURITY": {
        "household": [
            "We stretch groceries and sometimes skip meals so tuition can stay current.",
            "Food insecurity is creeping back—we rely on the pantry between paychecks.",
            "I water down meals for the kids when food runs low after rent and child care.",
        ],
        "provider": [
            "Families tell me they face food insecurity, and we set up snack pantries in the classroom.",
            "I see children coming in hungry, and our program scrambles to cover snacks.",
            "Food budgets for the program are maxed out while families ask for extra meals.",
        ],
    },
    "CHILDCARE_ACCESS": {
        "household": [
            "We have been on a childcare waitlist for months after our center closed.",
            "No slots open when my shifts change, so reliable childcare access feels impossible.",
            "Finding after-school care is a battle every semester, and options keep shrinking.",
        ],
        "provider": [
            "Families want more slots than we can offer; access breaks down when staff call out.",
            "Our center closed classrooms temporarily, so neighborhood access evaporated.",
            "I field calls daily from parents desperate for openings we just do not have.",
        ],
    },
    "AFFORDABILITY": {
        "household": [
            "Tuition and fees are too expensive; every increase means cutting groceries.",
            "We cannot afford reliable care when costs rise faster than wages.",
            "Childcare remains unaffordable, forcing us to take turns missing work.",
        ],
        "provider": [
            "Operating costs skyrocket but families cannot absorb more tuition.",
            "Affordability pressures mean delays in payments and tighter margins for the program.",
            "Keeping care affordable while paying staff fairly is nearly impossible.",
        ],
    },
    "EMPLOYMENT_DISRUPTION": {
        "household": [
            "I miss work every time care falls through, and my employer is losing patience.",
            "My hours were cut after too many schedule changes driven by childcare gaps.",
            "Employment keeps getting disrupted when I have to leave early for pickups.",
        ],
        "provider": [
            "I am juggling second jobs because enrollment swings disrupt my own employment stability.",
            "Assistants quit when schedules change, so my employment feels precarious too.",
            "Staff juggle multiple jobs, and every disruption ripples through coverage.",
        ],
    },
    "PROVIDER_STAFF_SHORTAGE": {
        "household": [
            "Our center says classrooms merge because of staff shortages, leaving fewer hours.",
            "Short staffing means inconsistent caregivers and unpredictable schedules for us.",
            "We were told staffing shortages limit the program to part-week care.",
        ],
        "provider": [
            "We are short staffed and cannot hire assistants even after months of recruiting.",
            "No substitutes are available, so I cover multiple classrooms daily.",
            "Open positions stay vacant, forcing us to cap enrollment and reduce hours.",
        ],
    },
    "SCHEDULING_CONSTRAINTS": {
        "household": [
            "My split shift schedule never aligns with the center's hours, so coverage falls apart.",
            "Weekend work is non-negotiable, but there is no evening care anywhere nearby.",
            "Coordinating schedules with my partner and the provider is a weekly puzzle we rarely solve.",
        ],
        "provider": [
            "Families need nights and weekend coverage, but we cannot stretch schedules without burning out staff.",
            "Coordinating staggered shifts with limited staff feels impossible.",
            "Scheduling constraints force us to close early when multiple people call out.",
        ],
    },
}


@dataclass(frozen=True)
class SyntheticConfig:
    """Configuration for generating deterministic survey data."""

    num_responses: int
    num_waves: int
    seed: int

    def validate(self) -> None:
        if self.num_responses <= 0:
            raise ValueError("num_responses must be positive")
        if not 1 <= self.num_waves <= len(MONTHS):
            raise ValueError("num_waves must be between 1 and 3 for Jan–Mar 2024")


def _compose_response(frame: str, rng: np.random.Generator) -> str:
    theme_count = int(rng.integers(1, 4))
    theme_names = rng.choice(list(THEME_SNIPPETS.keys()), size=theme_count, replace=False)
    snippets = []
    for theme in theme_names:
        phrases = THEME_SNIPPETS[theme][frame]
        snippets.append(rng.choice(phrases))
    return " ".join(snippets)


def generate_synthetic_responses(
    num_responses: int = 2000,
    num_waves: int = 3,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate synthetic qualitative survey responses across multiple waves.

    Args:
        num_responses: Total number of open-ended responses to create.
        num_waves: Number of survey waves (Jan–Mar 2024).
        seed: Deterministic random seed.

    Returns:
        Pandas DataFrame with household and provider frames plus narrative text.
    """

    config = SyntheticConfig(num_responses=num_responses, num_waves=num_waves, seed=seed)
    config.validate()

    rng = np.random.default_rng(seed)
    months = MONTHS[: config.num_waves]

    records: List[Dict[str, str]] = []
    for idx in range(config.num_responses):
        frame = str(rng.choice(FRAMES, p=FRAME_WEIGHTS))
        wave = int(rng.integers(1, config.num_waves + 1))
        survey_month = months[wave - 1]
        state = str(rng.choice(STATES))

        income_bracket = str(rng.choice(HOUSEHOLD_INCOME, p=HOUSEHOLD_INCOME_WEIGHTS)) if frame == "household" else None
        provider_setting = str(rng.choice(PROVIDER_SETTINGS, p=PROVIDER_SETTING_WEIGHTS)) if frame == "provider" else None

        open_response_text = _compose_response(frame=frame, rng=rng)

        records.append(
            {
                "respondent_id": f"R{idx + 1:05d}",
                "frame": frame,
                "wave": wave,
                "survey_month": survey_month,
                "state": state,
                "income_bracket": income_bracket,
                "provider_setting": provider_setting,
                "open_response_text": open_response_text,
            }
        )

    return pd.DataFrame.from_records(records)


__all__ = ["generate_synthetic_responses", "SyntheticConfig"]
