"""
Analiza rezultatelor si generare grafice.
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from simulation.models import TriageLevel


# Stil grafice
sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)
COLORS = {
    "FIFO": "#5C768D",
    "Priority Strict": "#A5525A",
    "Priority + FIFO": "#558A7A",
    "SJF (Shortest Job First)": "#7F6294",
    "Round Robin Ponderat": "#C0865C",
}

LEVEL_COLORS = {
    1: "#C25953",   # Rosu
    2: "#D4AC0D",   # Galben
    3: "#52BE80",   # Verde
    4: "#5DADE2",   # Albastru
    5: "#BDC3C7",   # Alb
}


def analyze_results(all_results: list[dict], output_dir: str = "results"):
    """Analizeaza rezultatele si genereaza CSV + grafice."""
    os.makedirs(output_dir, exist_ok=True)

    df = pd.DataFrame(all_results)

    # Export CSV
    csv_path = os.path.join(output_dir, "results.csv")
    df.to_csv(csv_path, index=False)
    print(f"\n  Rezultate salvate in: {csv_path}")

    # Tabel sumar
    summary = _compute_summary(df)
    summary_path = os.path.join(output_dir, "summary.csv")
    summary.to_csv(summary_path, index=False)
    print(f"  Sumar salvat in: {summary_path}")
    _print_summary_table(summary)

    # Grafice
    _plot_avg_waiting_time(df, output_dir)
    _plot_waiting_by_level(df, output_dir)
    _plot_los_boxplot(df, output_dir)
    _plot_target_compliance(df, output_dir)
    _plot_waiting_time_heatmap(df, output_dir)

    print(f"\n  Grafice salvate in: {output_dir}/")
    return summary


def _compute_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Calculeaza statistici sumare per strategie."""
    rows = []
    for strategy_name, group in df.groupby("strategy"):
        row = {"strategy": strategy_name}

        for metric in ["avg_waiting_time", "avg_los", "total_patients", "target_compliance"]:
            values = group[metric].values
            mean = np.mean(values)
            ci = stats.t.interval(0.95, len(values) - 1, loc=mean, scale=stats.sem(values))

            row[f"{metric}_mean"] = round(mean, 2)
            row[f"{metric}_ci_low"] = round(ci[0], 2)
            row[f"{metric}_ci_high"] = round(ci[1], 2)

        rows.append(row)
    return pd.DataFrame(rows)


def _print_summary_table(summary: pd.DataFrame):
    """Afiseaza tabelul sumar in consola."""
    print("\n" + "=" * 85)
    print(f"  {'Strategie':<28} {'Asteptare (min)':<20} {'LOS (min)':<20} {'Tinta (%)':<15}")
    print("-" * 85)
    for _, row in summary.iterrows():
        wait = f"{row['avg_waiting_time_mean']:.1f} [{row['avg_waiting_time_ci_low']:.1f}-{row['avg_waiting_time_ci_high']:.1f}]"
        los = f"{row['avg_los_mean']:.1f} [{row['avg_los_ci_low']:.1f}-{row['avg_los_ci_high']:.1f}]"
        target = f"{row['target_compliance_mean']:.1f}%"
        print(f"  {row['strategy']:<28} {wait:<20} {los:<20} {target:<15}")
    print("=" * 85)


def _plot_avg_waiting_time(df: pd.DataFrame, output_dir: str):
    """Grafic 1: Timp mediu de asteptare per strategie (bar chart cu CI)."""
    fig, ax = plt.subplots(figsize=(10, 6))

    strategies = df["strategy"].unique()
    means, cis = [], []
    for s in strategies:
        vals = df[df["strategy"] == s]["avg_waiting_time"].values
        means.append(np.mean(vals))
        ci = stats.t.interval(0.95, len(vals) - 1, loc=np.mean(vals), scale=stats.sem(vals))
        cis.append(np.mean(vals) - ci[0])

    colors = [COLORS.get(s, "#888888") for s in strategies]
    bars = ax.bar(strategies, means, yerr=cis, capsize=5, color=colors, edgecolor="white", linewidth=1.5)

    ax.set_ylabel("Timp mediu de asteptare (minute)")
    ax.set_title("Comparatie strategii — Timp mediu de asteptare")
    ax.set_xticklabels(strategies, rotation=15, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "1_avg_waiting_time.png"), dpi=150)
    plt.close()


def _plot_waiting_by_level(df: pd.DataFrame, output_dir: str):
    """Grafic 2: Timp de asteptare per nivel triaj × strategie (grouped bar)."""
    fig, ax = plt.subplots(figsize=(12, 6))

    strategies = df["strategy"].unique()
    x = np.arange(len(strategies))
    width = 0.15

    for i, level in enumerate(TriageLevel):
        col = f"level_{level.value}_avg_wait"
        means = [df[df["strategy"] == s][col].mean() for s in strategies]
        ax.bar(x + i * width, means, width, label=f"Nivel {level.value} ({level.color_name})",
               color=LEVEL_COLORS[level.value], edgecolor="white")

    ax.set_xticks(x + width * 2)
    ax.set_xticklabels(strategies, rotation=15, ha="right")
    ax.set_ylabel("Timp mediu de asteptare (minute)")
    ax.set_title("Timp de asteptare per nivel de triaj si strategie")
    ax.legend(title="Nivel triaj")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "2_waiting_by_level.png"), dpi=150)
    plt.close()


def _plot_los_boxplot(df: pd.DataFrame, output_dir: str):
    """Grafic 3: Distributia LOS per strategie (box plot)."""
    fig, ax = plt.subplots(figsize=(10, 6))

    palette = [COLORS.get(s, "#888888") for s in df["strategy"].unique()]
    sns.boxplot(data=df, x="strategy", y="avg_los", palette=palette, ax=ax)

    ax.set_xlabel("")
    ax.set_ylabel("Timp mediu in sistem - LOS (minute)")
    ax.set_title("Distributia Length of Stay per strategie")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=15, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "3_los_boxplot.png"), dpi=150)
    plt.close()


def _plot_target_compliance(df: pd.DataFrame, output_dir: str):
    """Grafic 4: Conformitate cu timpul tinta per nivel si strategie."""
    fig, ax = plt.subplots(figsize=(12, 6))

    strategies = df["strategy"].unique()
    x = np.arange(len(strategies))
    width = 0.15

    for i, level in enumerate(TriageLevel):
        col = f"level_{level.value}_target_compliance"
        means = [df[df["strategy"] == s][col].mean() for s in strategies]
        ax.bar(x + i * width, means, width, label=f"Nivel {level.value} ({level.color_name})",
               color=LEVEL_COLORS[level.value], edgecolor="white")

    ax.set_xticks(x + width * 2)
    ax.set_xticklabels(strategies, rotation=15, ha="right")
    ax.set_ylabel("Conformitate cu timpul tinta (%)")
    ax.set_title("Procentul pacientilor tratati in timpul tinta per nivel si strategie")
    ax.legend(title="Nivel triaj")
    ax.set_ylim(0, 105)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "4_target_compliance.png"), dpi=150)
    plt.close()


def _plot_waiting_time_heatmap(df: pd.DataFrame, output_dir: str):
    """Grafic 5: Heatmap — timp mediu asteptare (strategie × nivel triaj)."""
    strategies = df["strategy"].unique()
    data = []
    for s in strategies:
        row = []
        for level in TriageLevel:
            col = f"level_{level.value}_avg_wait"
            row.append(df[df["strategy"] == s][col].mean())
        data.append(row)

    heatmap_df = pd.DataFrame(
        data,
        index=strategies,
        columns=[f"Nivel {l.value}\n({l.color_name})" for l in TriageLevel],
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(heatmap_df, annot=True, fmt=".1f", cmap="YlOrRd", ax=ax,
                linewidths=1, linecolor="white", cbar_kws={"label": "Minute"})
    ax.set_title("Heatmap — Timp mediu de asteptare (minute)")
    ax.set_ylabel("Strategie")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "5_heatmap.png"), dpi=150)
    plt.close()
