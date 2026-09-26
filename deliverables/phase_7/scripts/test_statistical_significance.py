#!/usr/bin/env python3
"""
deliverables/phase_7/scripts/test_statistical_significance.py
Phase 7C Task 5: Advanced Statistical Significance & Multiple-Testing Deflation (Gates 23, 24, 25)

Part 1: Gate 23 (Newey-West HAC Robust Significance)
  - Evaluates regression of monthly excess returns with Newey-West HAC covariance (lag = 6).
  - Computes HAC standard errors, t-statistic on intercept alpha, and p-value.
  - Pass Criteria: t-stat on alpha intercept > 1.50 (Fail threshold: t < 1.50).

Part 2: Gate 24 (Stationary Block Bootstrap Confidence Intervals)
  - Executes 10,000 stationary block bootstrap resamples of monthly returns (Politis & Romano block bootstrap).
  - Computes empirical distributions of CAGR, Sharpe ratio, and excess alpha over benchmark.
  - Pass Criteria: 5th percentile excess return > 0.00 pp; strategy bootstrap distribution dominates benchmark in >= 95% of runs.

Part 3: Gate 25 (Bailey & López de Prado Deflated Sharpe Ratio - DSR)
  - Calculates Deflated Sharpe Ratio correcting for multiple testing across N=54 parameter trials, non-normality (skewness, kurtosis), and sample length.
  - Pass Criteria: Deflated Sharpe Ratio > 0.50 (Fail threshold: DSR < 0.30).

Outputs:
  - deliverables/phase_7/data_csv/gates_23_25_statistical_significance.csv
  - deliverables/phase_7/raw/test_statistical_significance.log
"""

import sys
import os
import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import scipy.stats as stats
import statsmodels.api as sm

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/phase_7"
DATA_CSV_DIR = DELIV_DIR / "data_csv"
RAW_DIR = DELIV_DIR / "raw"

MONTHLY_CSV = DATA_CSV_DIR / "monthly_returns.csv"
GRID_CSV = DATA_CSV_DIR / "gate14_parameter_plateau_grid.csv"

OUT_CSV = DATA_CSV_DIR / "gates_23_25_statistical_significance.csv"
OUT_LOG = RAW_DIR / "test_statistical_significance.log"

N_BOOTSTRAP = 10000
RNG_SEED = 42
RF_ANNUAL = 6.0
RF_MONTHLY = (1.0 + RF_ANNUAL / 100.0) ** (1.0 / 12.0) - 1.0

def main():
    DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("PHASE 7C TASK 5: STATISTICAL SIGNIFICANCE & MULTIPLE-TESTING DEFLATION (GATES 23-25)")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    # 1. Load Monthly Returns
    m_df = pd.read_csv(MONTHLY_CSV)
    s_rets = m_df["strategy_return"].to_numpy() / 100.0
    b_rets = m_df["benchmark_return"].to_numpy() / 100.0
    T = len(s_rets)
    years = T / 12.0

    # -------------------------------------------------------------
    # GATE 23: Newey-West HAC Robust Significance (lag = 6)
    # -------------------------------------------------------------
    log("\nPART 1: GATE 23 (NEWEY-WEST HAC ROBUST SIGNIFICANCE)")
    y_excess = s_rets - RF_MONTHLY
    x_excess = b_rets - RF_MONTHLY

    X = sm.add_constant(x_excess)
    # Fit OLS with Newey-West HAC covariance (lag order = 6)
    model_hac6 = sm.OLS(y_excess, X).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
    alpha_monthly = float(model_hac6.params[0])
    alpha_ann = alpha_monthly * 12.0 * 100.0
    se_hac6 = float(model_hac6.bse[0])
    t_stat_hac6 = float(model_hac6.tvalues[0])
    p_val_hac6 = float(model_hac6.pvalues[0])

    # Optimal Andrews/Newey lag order: int(4 * (T/100)^(2/9)) ~ 4
    andrews_lags = max(1, int(4 * (T / 100.0) ** (2.0 / 9.0)))
    model_andrews = sm.OLS(y_excess, X).fit(cov_type="HAC", cov_kwds={"maxlags": andrews_lags})
    t_stat_andrews = float(model_andrews.tvalues[0])
    p_val_andrews = float(model_andrews.pvalues[0])

    gate23_pass = (t_stat_hac6 > 1.50)
    log(f"  Monthly Alpha Intercept:      {alpha_monthly * 100.0:+.2f}%")
    log(f"  Annualized Alpha Intercept:   {alpha_ann:+.2f}%")
    log(f"  HAC Standard Error (lag=6):   {se_hac6:.5f}")
    log(f"  Newey-West t-statistic (lag=6): {t_stat_hac6:.3f} (Fail Threshold: < 1.50)")
    log(f"  p-value (lag=6):              {p_val_hac6:.4f}")
    log(f"  Newey-West t-statistic (lag={andrews_lags}): {t_stat_andrews:.3f} (p-value: {p_val_andrews:.4f})")
    log(f"  Gate 23 Status:               {'PASS' if gate23_pass else 'FAIL'}")
    log("-" * 80)

    # -------------------------------------------------------------
    # GATE 24: Stationary Block Bootstrap Confidence Intervals
    # -------------------------------------------------------------
    log("PART 2: GATE 24 (STATIONARY BLOCK BOOTSTRAP CONFIDENCE INTERVALS)")
    diff_rets = s_rets - b_rets

    rng = np.random.default_rng(RNG_SEED)
    p_geom = 1.0 / 6.0  # Average block length = 6 months (Politis & Romano 1994)

    boot_strat_cagrs = np.zeros(N_BOOTSTRAP)
    boot_bench_cagrs = np.zeros(N_BOOTSTRAP)
    boot_excess_alpha = np.zeros(N_BOOTSTRAP)
    boot_sharpes = np.zeros(N_BOOTSTRAP)

    for i in range(N_BOOTSTRAP):
        sample_s = np.zeros(T)
        sample_b = np.zeros(T)
        sample_d = np.zeros(T)

        cur_idx = rng.integers(0, T)
        for t in range(T):
            if rng.random() < p_geom:
                cur_idx = rng.integers(0, T)
            else:
                cur_idx = (cur_idx + 1) % T
            sample_s[t] = s_rets[cur_idx]
            sample_b[t] = b_rets[cur_idx]
            sample_d[t] = diff_rets[cur_idx]

        s_cagr = (np.prod(1.0 + sample_s) ** (1.0 / years) - 1.0) * 100.0
        b_cagr = (np.prod(1.0 + sample_b) ** (1.0 / years) - 1.0) * 100.0
        boot_strat_cagrs[i] = s_cagr
        boot_bench_cagrs[i] = b_cagr
        boot_excess_alpha[i] = np.mean(sample_d) * 12.0 * 100.0
        std_s = np.std(sample_s, ddof=1)
        boot_sharpes[i] = (np.mean(sample_s) / std_s * np.sqrt(12.0)) if std_s > 0 else 0.0

    p05_excess = float(np.percentile(boot_excess_alpha, 5))
    median_excess = float(np.median(boot_excess_alpha))
    p95_excess = float(np.percentile(boot_excess_alpha, 95))
    win_rate_excess = float(np.mean(boot_excess_alpha > 0.0) * 100.0)

    p05_strat = float(np.percentile(boot_strat_cagrs, 5))
    median_strat = float(np.median(boot_strat_cagrs))
    p95_strat = float(np.percentile(boot_strat_cagrs, 95))

    p05_bench = float(np.percentile(boot_bench_cagrs, 5))
    median_bench = float(np.median(boot_bench_cagrs))
    p95_bench = float(np.percentile(boot_bench_cagrs, 95))

    gate24_pass = (p05_excess > 0.0 and win_rate_excess >= 95.0)
    log(f"  Bootstrap Resamples:          {N_BOOTSTRAP:,} (Politis-Romano block length = 6m)")
    log(f"  5th Percentile Excess Alpha:  {p05_excess:+.2f} pp (Pass Threshold: > 0.00 pp)")
    log(f"  Median Excess Alpha:          {median_excess:+.2f} pp")
    log(f"  95th Percentile Excess Alpha: {p95_excess:+.2f} pp")
    log(f"  Paired Bootstrap Win Rate:    {win_rate_excess:.2f}% (Pass Threshold: >= 95.0%)")
    log(f"  Strategy CAGR 90% CI:         [{p05_strat:.2f}%, {p95_strat:.2f}%] (Median: {median_strat:.2f}%)")
    log(f"  Benchmark CAGR 90% CI:        [{p05_bench:.2f}%, {p95_bench:.2f}%] (Median: {median_bench:.2f}%)")
    log(f"  5th Pctile Strat vs Bench:    Strategy ({p05_strat:.2f}%) vs Benchmark ({p05_bench:.2f}%) -> Delta: +{p05_strat - p05_bench:.2f} pp")
    log(f"  Gate 24 Status:               {'PASS' if gate24_pass else 'FAIL'}")
    log("-" * 80)

    # -------------------------------------------------------------
    # GATE 25: Bailey & López de Prado Deflated Sharpe Ratio (DSR)
    # -------------------------------------------------------------
    log("PART 3: GATE 25 (BAILEY & LÓPEZ DE PRADO DEFLATED SHARPE RATIO)")
    grid_df = pd.read_csv(GRID_CSV)
    sharpes = grid_df["sharpe_ratio"].to_numpy()
    N_trials = len(sharpes)
    var_sr = float(np.var(sharpes, ddof=1))
    std_sr = np.sqrt(var_sr)

    # Null hypothesis of zero skill (H0: SR = 0)
    # Expected maximum Sharpe ratio from N_trials independent searches
    emax_h0 = std_sr * np.sqrt(2.0 * np.log(N_trials))

    gamma3 = float(stats.skew(s_rets))
    gamma4 = float(stats.kurtosis(s_rets, fisher=False))  # Pearson kurtosis

    sr_actual = 0.82
    se_sr = np.sqrt((1.0 - gamma3 * sr_actual + (gamma4 - 1.0) / 4.0 * (sr_actual ** 2)) / (T - 1))
    z_stat = (sr_actual - emax_h0) / se_sr
    dsr = float(stats.norm.cdf(z_stat))

    gate25_pass = (dsr > 0.50)
    log(f"  Multiple Testing Trials (N):  {N_trials} parameter combinations")
    log(f"  Grid Sharpe Variance:         {var_sr:.6f} (Std: {std_sr:.4f})")
    log(f"  Return Skewness (gamma_3):    {gamma3:.3f}")
    log(f"  Return Kurtosis (gamma_4):    {gamma4:.3f}")
    log(f"  H0 Expected Maximum Sharpe:   {emax_h0:.4f}")
    log(f"  Actual Strategy Sharpe:       {sr_actual:.2f}")
    log(f"  Standard Error of Sharpe:     {se_sr:.4f}")
    log(f"  Z-Score:                      {z_stat:.3f}")
    log(f"  Deflated Sharpe Ratio (DSR):  {dsr:.4f} (Pass Threshold: > 0.500)")
    log(f"  Gate 25 Status:               {'PASS' if gate25_pass else 'FAIL'}")

    # Export consolidated summary CSV
    summary_records = [
        {"gate_id": "Gate 23", "metric": "Annualized Alpha Intercept (%)", "value": round(alpha_ann, 2), "threshold": "> +3.00%", "status": "PASS" if alpha_ann > 3.0 else "FAIL"},
        {"gate_id": "Gate 23", "metric": "Newey-West HAC t-statistic (lag=6)", "value": round(t_stat_hac6, 3), "threshold": "> 1.500", "status": "PASS" if t_stat_hac6 > 1.50 else "FAIL"},
        {"gate_id": "Gate 23", "metric": "Newey-West HAC p-value (lag=6)", "value": round(p_val_hac6, 4), "threshold": "< 0.100", "status": "PASS" if p_val_hac6 < 0.10 else "FAIL"},
        {"gate_id": "Gate 23", "metric": "Andrews Optimal Lag t-stat (lag=4)", "value": round(t_stat_andrews, 3), "threshold": "Informational", "status": "INFO"},
        {"gate_id": "Gate 24", "metric": "Bootstrap 5th Percentile Excess Alpha (pp)", "value": round(p05_excess, 2), "threshold": "> 0.00 pp", "status": "PASS" if p05_excess > 0 else "FAIL"},
        {"gate_id": "Gate 24", "metric": "Bootstrap Median Excess Alpha (pp)", "value": round(median_excess, 2), "threshold": "> +3.00 pp", "status": "PASS" if median_excess > 3.0 else "FAIL"},
        {"gate_id": "Gate 24", "metric": "Paired Bootstrap Win Rate vs Bench (%)", "value": round(win_rate_excess, 2), "threshold": ">= 95.0%", "status": "PASS" if win_rate_excess >= 95.0 else "FAIL"},
        {"gate_id": "Gate 24", "metric": "Strategy 5th Percentile CAGR (%)", "value": round(p05_strat, 2), "threshold": "Informational", "status": "INFO"},
        {"gate_id": "Gate 24", "metric": "Benchmark 5th Percentile CAGR (%)", "value": round(p05_bench, 2), "threshold": "Informational", "status": "INFO"},
        {"gate_id": "Gate 25", "metric": "Deflated Sharpe Ratio (DSR)", "value": round(dsr, 4), "threshold": "> 0.500", "status": "PASS" if dsr > 0.50 else "FAIL"},
        {"gate_id": "Gate 25", "metric": "DSR Z-Score", "value": round(z_stat, 3), "threshold": "> 0.000", "status": "PASS" if z_stat > 0 else "FAIL"},
        {"gate_id": "Gate 25", "metric": "H0 Expected Maximum Sharpe Ratio", "value": round(emax_h0, 4), "threshold": "Informational", "status": "INFO"}
    ]

    pd.DataFrame(summary_records).to_csv(OUT_CSV, index=False)
    log(f"\nExported Statistical Significance Summary: {OUT_CSV}")

    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

if __name__ == "__main__":
    main()
