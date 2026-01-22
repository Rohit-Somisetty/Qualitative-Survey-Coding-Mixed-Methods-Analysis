"""Create a reviewer-friendly demo bundle of key qualitative outputs."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:  # pragma: no cover - runtime convenience
    sys.path.append(str(PROJECT_ROOT))

from src.run_pipeline import run_pipeline  # type: ignore


def _rewrite_fig_paths(html_path: Path) -> None:
    text = html_path.read_text(encoding="utf-8")
    updated = text.replace("factsheet_assets/figures/", "figures/")
    html_path.write_text(updated, encoding="utf-8")


def export_demo_assets(
    base_dir: Path | None = None,
    responses: int = 800,
    waves: int = 3,
    seed: int = 42,
) -> None:
    base = Path(base_dir) if base_dir is not None else Path(__file__).resolve().parents[1]
    run_pipeline(responses=responses, waves=waves, seed=seed, base_dir=base)

    demo_dir = base / "docs" / "demo"
    demo_dir.mkdir(parents=True, exist_ok=True)

    files_to_copy = {
        base / "reports" / "qual_factsheet_latest.html": demo_dir / "qual_factsheet_latest.html",
        base / "docs" / "qualitative_brief.md": demo_dir / "qualitative_brief.md",
        base / "data" / "outputs" / "reliability_by_theme.csv": demo_dir / "reliability_by_theme.csv",
    }

    for src, dest in files_to_copy.items():
        if src.exists():
            shutil.copyfile(src, dest)

    figures_src = base / "reports" / "factsheet_assets" / "figures"
    figures_dest = demo_dir / "figures"
    if figures_src.exists():
        if figures_dest.exists():
            shutil.rmtree(figures_dest)
        shutil.copytree(figures_src, figures_dest)

    html_demo = demo_dir / "qual_factsheet_latest.html"
    if html_demo.exists():
        _rewrite_fig_paths(html_demo)

    readme = demo_dir / "README_demo.md"
    readme.write_text(
        "# Demo bundle\n\n"
        "This folder contains ready-to-share artifacts generated from the synthetic qualitative pipeline.\n\n"
        "## Files\n"
        "- qual_factsheet_latest.html: one-page mixed-methods fact sheet (figures referenced in ./figures).\n"
        "- qualitative_brief.md: narrative brief with key themes, co-occurrences, and mixed-methods highlights.\n"
        "- reliability_by_theme.csv: percent agreement and Cohen's kappa per theme.\n"
        "- figures/: PNG assets embedded in the fact sheet.\n\n"
        "## Regenerate\n"
        "Run `python scripts/export_demo_assets.py` (or call export_demo_assets()) to rebuild with fresh synthetic data.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Export reviewer-friendly demo assets.")
    parser.add_argument("--responses", type=int, default=800)
    parser.add_argument("--waves", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    export_demo_assets(responses=args.responses, waves=args.waves, seed=args.seed)


if __name__ == "__main__":
    main()
