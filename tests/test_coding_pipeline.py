"""Smoke tests for the qualitative pipeline and Step B artifacts."""
from pathlib import Path

import pandas as pd

from src.generate_qual_data import generate_synthetic_responses
from src.preprocess_text import preprocess_series
from src.run_pipeline import run_pipeline
from scripts.export_demo_assets import export_demo_assets


def test_generate_synthetic_responses_shape(tmp_path):
    df = generate_synthetic_responses(num_responses=120, num_waves=3, seed=42)
    expected_columns = {
        "respondent_id",
        "frame",
        "wave",
        "survey_month",
        "state",
        "income_bracket",
        "provider_setting",
        "open_response_text",
    }
    assert len(df) == 120
    assert expected_columns.issubset(df.columns)
    assert set(df["frame"].unique()).issubset({"household", "provider"})
    assert df["wave"].between(1, 3).all()


def test_preprocess_series_handles_missing_values():
    raw = pd.Series(["Stress is overwhelming!", None, "", "Childcare costs are too expensive."])
    cleaned = preprocess_series(raw)
    assert cleaned.iloc[0].startswith("stress")
    assert cleaned.iloc[1] == ""
    assert cleaned.iloc[2] == ""
    assert "cost" in cleaned.iloc[3]


def test_pipeline_generates_mixed_methods_outputs(tmp_path):
    base_dir = tmp_path / "qual_project"
    base_dir.mkdir(parents=True)

    run_pipeline(responses=150, waves=3, seed=42, base_dir=base_dir)

    processed_dir = base_dir / "data" / "processed"
    outputs_dir = base_dir / "data" / "outputs"
    figures_dir = base_dir / "reports" / "figures"
    docs_dir = base_dir / "docs"
    reports_dir = base_dir / "reports"

    wide_path = processed_dir / "coded_responses_wide.csv"
    long_path = processed_dir / "coded_responses_long.csv"
    exemplar_path = outputs_dir / "exemplar_quotes.csv"
    summary_path = outputs_dir / "mixed_methods_summary.csv"
    reliability_path = outputs_dir / "reliability_by_theme.csv"
    factsheet_path = reports_dir / "qual_factsheet_latest.html"

    assert wide_path.exists()
    assert long_path.exists()

    exemplars = pd.read_csv(exemplar_path)
    assert exemplars["theme"].nunique() >= 3

    summary = pd.read_csv(summary_path)
    assert {"household", "provider"}.issubset(set(summary["frame"].unique()))

    reliability_df = pd.read_csv(reliability_path)
    assert "kappa" in reliability_df.columns

    factsheet_text = factsheet_path.read_text(encoding="utf-8")
    assert "Reliability" in factsheet_text

    figure_files = list(figures_dir.glob("*.png"))
    assert len(figure_files) >= 3

    brief_path = docs_dir / "qualitative_brief.md"
    brief_text = brief_path.read_text(encoding="utf-8")
    assert "Exemplar quotes" in brief_text
    assert "Mixed-methods highlights" in brief_text

    export_demo_assets(base_dir=base_dir, responses=120, waves=3, seed=42)
    demo_dir = base_dir / "docs" / "demo"
    assert (demo_dir / "qual_factsheet_latest.html").exists()
    assert (demo_dir / "figures").is_dir()
    assert (demo_dir / "reliability_by_theme.csv").exists()
