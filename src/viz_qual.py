"""Visualization utilities for qualitative and mixed-methods outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _plot_theme_frequencies_trend(df: pd.DataFrame, output_path: Path, top_n: int = 6) -> None:
    if df.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, "No frequency data", ha="center", va="center")
        ax.axis("off")
        fig.savefig(output_path, dpi=300)
        plt.close(fig)
        return
    df["percent"] = df["percent"].astype(float).fillna(0)
    totals = df.groupby("theme", as_index=False)["count"].sum().sort_values(by="count", ascending=False)
    top_themes = totals.head(top_n)["theme"].tolist()
    plot_df = df[df["theme"].isin(top_themes)]
    frames = sorted(plot_df["frame"].unique())
    if not frames:
        frames = sorted(df["frame"].unique())
    fig, axes = plt.subplots(1, len(frames) or 1, figsize=(6 * max(len(frames), 1), 4), sharey=True)
    if not isinstance(axes, np.ndarray):
        axes = np.array([axes])
    for ax, frame in zip(axes, frames):
        frame_df = plot_df[plot_df["frame"] == frame]
        for theme in top_themes:
            theme_df = frame_df[frame_df["theme"] == theme].sort_values("wave")
            if theme_df.empty:
                continue
            ax.plot(theme_df["wave"], theme_df["percent"] * 100, marker="o", label=theme)
        ax.set_title(f"{frame.title()} themes")
        ax.set_xlabel("Wave")
        ax.set_ylabel("Percent of responses")
        ax.grid(True, alpha=0.3)
    axes[0].legend(loc="upper right", fontsize=8)
    fig.suptitle("Theme frequency trends by frame")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def _plot_theme_cooccurrence_heatmap(df: pd.DataFrame, output_path: Path) -> None:
    if df.empty:
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.text(0.5, 0.5, "No co-occurrence data", ha="center", va="center")
        ax.axis("off")
        fig.savefig(output_path, dpi=300)
        plt.close(fig)
        return
    themes = sorted(set(df["theme_a"]).union(df["theme_b"]))
    size = len(themes)
    matrix = np.zeros((size, size))
    theme_index = {theme: idx for idx, theme in enumerate(themes)}
    for _, row in df.iterrows():
        i = theme_index[row["theme_a"]]
        j = theme_index[row["theme_b"]]
        matrix[i, j] = row["count"]
        matrix[j, i] = row["count"]
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(range(size))
    ax.set_xticklabels(themes, rotation=45, ha="right")
    ax.set_yticks(range(size))
    ax.set_yticklabels(themes)
    ax.set_title("Theme co-occurrence counts")
    fig.colorbar(im, ax=ax, shrink=0.8, label="Count")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def _plot_stress_by_theme(summary_df: pd.DataFrame, output_path: Path, top_n: int = 6) -> None:
    df = summary_df[summary_df["metric"] == "stress_score_mean"]
    if df.empty:
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.text(0.5, 0.5, "No mixed-methods data", ha="center", va="center")
        ax.axis("off")
        fig.savefig(output_path, dpi=300)
        plt.close(fig)
        return
    present = df[df["group"] == "theme_present"].groupby("theme")["estimate"].mean()
    absent = df[df["group"] == "theme_absent"].groupby("theme")["estimate"].mean()
    common_themes = present.index.intersection(absent.index)
    if common_themes.empty:
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.text(0.5, 0.5, "Insufficient stress data", ha="center", va="center")
        ax.axis("off")
        fig.savefig(output_path, dpi=300)
        plt.close(fig)
        return
    diff = (present - absent).abs().sort_values(ascending=False)
    top_themes = diff.head(top_n).index
    plot_present = present[top_themes]
    plot_absent = absent[top_themes]

    x = np.arange(len(top_themes))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(x - width / 2, plot_absent, width, label="Theme absent", color="#cfd8dc")
    ax.bar(x + width / 2, plot_present, width, label="Theme present", color="#546e7a")
    ax.set_xticks(x)
    ax.set_xticklabels(top_themes, rotation=30, ha="right")
    ax.set_ylabel("Mean stress score")
    ax.set_title("Stress score by theme presence")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def generate_visualizations(
    theme_freq_path: str,
    cooccurrence_path: str,
    summary_path: str,
    figures_dir: str,
) -> Dict[str, str]:
    """Create PNG visualizations used in the portfolio brief."""

    figures_path = Path(figures_dir)
    figures_path.mkdir(parents=True, exist_ok=True)

    freq_df = pd.read_csv(theme_freq_path) if Path(theme_freq_path).exists() else pd.DataFrame()
    coocc_df = pd.read_csv(cooccurrence_path) if Path(cooccurrence_path).exists() else pd.DataFrame()
    summary_df = pd.read_csv(summary_path) if Path(summary_path).exists() else pd.DataFrame()

    freq_path = figures_path / "theme_frequencies_trend.png"
    coocc_path = figures_path / "theme_cooccurrence_heatmap.png"
    stress_path = figures_path / "mixed_methods_theme_vs_stress.png"

    _plot_theme_frequencies_trend(freq_df, freq_path)
    _plot_theme_cooccurrence_heatmap(coocc_df, coocc_path)
    _plot_stress_by_theme(summary_df, stress_path)

    return {
        "theme_frequencies_trend": str(freq_path),
        "theme_cooccurrence_heatmap": str(coocc_path),
        "mixed_methods_theme_vs_stress": str(stress_path),
    }


__all__ = ["generate_visualizations"]
