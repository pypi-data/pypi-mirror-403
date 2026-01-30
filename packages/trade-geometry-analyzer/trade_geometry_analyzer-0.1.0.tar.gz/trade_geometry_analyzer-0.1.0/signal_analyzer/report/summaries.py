"""Generate textual summaries and findings from trade geometry metrics."""

from typing import Dict, Any
from ..core.trades import TradeSet
from ..analysis.geometry import geometry_metrics


def format_geometry_summary(trades: TradeSet) -> str:
    """
    Generate a textual summary of trade geometry metrics.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data

    Returns
    -------
    str
        Formatted summary text
    """
    metrics = geometry_metrics(trades)

    summary = f"""
Trade Geometry Summary ({trades.side.upper()})
{'=' * 50}
Sample Size:        {metrics['n_trades']} trades

Central Tendency:
  Median MFE:       {metrics['median_mfe']:>6.2f}%
  Median MAE:       {metrics['median_mae']:>6.2f}%
  Mean MFE:         {metrics['mean_mfe']:>6.2f}%
  Mean MAE:         {metrics['mean_mae']:>6.2f}%

Win Rate:           {metrics['win_rate']*100:>6.2f}% (MFE > 0)

Tail Statistics:
  MFE 95th pct:     {metrics['mfe_p95']:>6.2f}%
  MFE 99th pct:     {metrics['mfe_p99']:>6.2f}%
  MAE  5th pct:     {metrics['mae_p5']:>6.2f}% (risk)
  MAE  1st pct:     {metrics['mae_p1']:>6.2f}% (extreme risk)

Correlation:
  MFE vs MAE:       {metrics['mfe_mae_corr']:>6.3f}
"""

    return summary


def generate_qualitative_findings(trades: TradeSet) -> list[str]:
    """
    Generate qualitative findings based on trade geometry metrics.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data

    Returns
    -------
    list of str
        List of qualitative finding statements
    """
    metrics = geometry_metrics(trades)
    findings = []

    # Edge assessment
    if metrics["median_mfe"] > 0:
        findings.append(
            f"✓ Signal shows positive median upside ({metrics['median_mfe']:.2f}%)"
        )
    else:
        findings.append(
            f"⚠ Signal shows no median upside ({metrics['median_mfe']:.2f}%)"
        )

    # Win rate assessment
    if metrics["win_rate"] > 0.6:
        findings.append(f"✓ High win rate ({metrics['win_rate']*100:.1f}%)")
    elif metrics["win_rate"] < 0.4:
        findings.append(
            f"⚠ Low win rate ({metrics['win_rate']*100:.1f}%) - needs strong asymmetry"
        )

    # Tail risk assessment
    mae_tail_ratio = abs(metrics["mae_p1"] / metrics["median_mae"]) if metrics["median_mae"] != 0 else 0
    if mae_tail_ratio > 3:
        findings.append(
            f"⚠ Significant tail risk detected (p1/median MAE ratio: {mae_tail_ratio:.1f}x)"
        )

    # Symmetry assessment
    if abs(metrics["mfe_mae_corr"]) < 0.3:
        findings.append(
            f"✓ Low MFE/MAE correlation ({metrics['mfe_mae_corr']:.2f}) - independent risk/reward"
        )
    elif metrics["mfe_mae_corr"] > 0.5:
        findings.append(
            f"⚠ High positive MFE/MAE correlation ({metrics['mfe_mae_corr']:.2f}) - big winners need big risk"
        )

    # Stop-friendliness heuristic
    median_dd = abs(metrics["median_mae"])
    if median_dd < 1.0:
        findings.append(
            f"✓ Tight-stop friendly (median drawdown: {median_dd:.2f}%)"
        )
    elif median_dd > 3.0:
        findings.append(
            f"⚠ Needs room - large median drawdown ({median_dd:.2f}%)"
        )

    # Upside potential
    if metrics["mfe_p95"] > 5 * abs(metrics["median_mae"]):
        findings.append(
            f"✓ Strong asymmetry: P95 MFE ({metrics['mfe_p95']:.2f}%) >> median risk"
        )

    return findings


def print_section_a_report(
    long_trades: TradeSet | None = None,
    short_trades: TradeSet | None = None,
) -> None:
    """
    Print a complete Section A (Geometry Overview) report.

    Parameters
    ----------
    long_trades : TradeSet, optional
        Long trade geometry data
    short_trades : TradeSet, optional
        Short trade geometry data
    """
    print("\n" + "=" * 70)
    print("SECTION A: GEOMETRY OVERVIEW")
    print("=" * 70)

    if long_trades is not None:
        print(format_geometry_summary(long_trades))
        print("\nQualitative Findings (Long):")
        for finding in generate_qualitative_findings(long_trades):
            print(f"  {finding}")

    if short_trades is not None:
        print("\n" + "-" * 70)
        print(format_geometry_summary(short_trades))
        print("\nQualitative Findings (Short):")
        for finding in generate_qualitative_findings(short_trades):
            print(f"  {finding}")

    print("\n" + "=" * 70)
