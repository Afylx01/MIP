#!/usr/bin/env python3
"""
run_mip.py
Project MIP — Unified Institutional Quantitative Workstation & Trading Desk.

An interactive Terminal User Interface (TUI) and unified CLI runner providing
instant access to all 18 institutional production, backtesting, analytics,
and audit workflows on the Samsung Galaxy S23 PRoot Ubuntu environment.

Usage:
  Interactive TUI:  python3 run_mip.py
  Direct Execution: python3 run_mip.py --option <0-18>
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional


def get_base_dir() -> Path:
    """Dynamically resolves Project MIP root across Windows and Linux."""
    if "PROJECT_MIP_DIR" in os.environ and Path(os.environ["PROJECT_MIP_DIR"]).exists():
        return Path(os.environ["PROJECT_MIP_DIR"])
    android_path = Path("/storage/emulated/0/Documents/Project MIP")
    if android_path.exists():
        return android_path
    cur = Path(__file__).resolve()
    for p in [cur] + list(cur.parents):
        if (p / "run_mip.py").exists() or (p / "data/universe").exists():
            return p
    return cur.parent


BASE_DIR = get_base_dir()
PYTHON_EXE = sys.executable or "python3"


# ANSI Colors & Styling
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
RED = "\033[31m"
WHITE = "\033[37m"

MENU_ITEMS = {
    # Live Production & Execution
    "1": {
        "title": "Run Weekly Momentum Scanner (Full Suite: Breadth + RRG + Sector Rotation)",
        "cmd": [PYTHON_EXE, str(BASE_DIR / "production/scanner.py")],
        "desc": "Runs 5-tier momentum screen, market breadth, sector rotation & candidate ranking."
    },
    "2": {
        "title": "Preview Telegram Execution Alert (Dry-Run ASCII/HTML Preview)",
        "cmd": [PYTHON_EXE, str(BASE_DIR / "production/telegram_alerts.py"), "--dry-run"],
        "desc": "Formats and prints complete HTML execution alert with character count check."
    },
    "3": {
        "title": "Dispatch Live Telegram Alert (Broadcast Signal to Channel)",
        "cmd": [PYTHON_EXE, str(BASE_DIR / "production/telegram_alerts.py")],
        "desc": "Dispatches official EOD momentum alert directly to user Telegram channel."
    },
    "4": {
        "title": "Generate Rebalance Orders & Manage Portfolio Ledger (Whole Shares & Fees)",
        "cmd": [PYTHON_EXE, str(BASE_DIR / "deliverables/phase_8/scripts/run_production_pipeline.py"), "--dual-date-simulation"],
        "desc": "Computes trade tickets, whole share sizing, statutory friction, and portfolio ledger."
    },
    "5": {
        "title": "Ingest Daily Bhavcopy & Update Master Universe Database",
        "cmd": [PYTHON_EXE, str(BASE_DIR / "scripts/update_universe.py")],
        "desc": "Ingests daily price bars, maintains survivorship-free database and updates metadata."
    },

    # Strategy Backtesting Lab
    "6": {
        "title": "Run Interactive Custom Backtest (Custom Dates, Top-N, Volar/Return, Exit Buffer)",
        "cmd": [PYTHON_EXE, str(BASE_DIR / "production/run_custom_backtest.py")],
        "desc": "Interactive parameterization for bespoke dates, allocation slots, and friction tiers."
    },
    "7": {
        "title": "Run Full 20-Year Baseline Backtest (2007–2026 Official Replay)",
        "cmd": [PYTHON_EXE, str(BASE_DIR / "deliverables/phase_7/scripts/init_phase7_engine.py")],
        "desc": "Replays official institutional benchmark proxy and validates calendar alignment."
    },
    "8": {
        "title": "Run 1,000-Iteration Monte Carlo Luck/Skill Test (p-value analysis)",
        "cmd": [PYTHON_EXE, str(BASE_DIR / "deliverables/phase_7/scripts/test_random_monte_carlo.py")],
        "desc": "Permutes trade sequences and computes p-values to prove alpha is not luck."
    },
    "9": {
        "title": "Run Institutional Cost & Slippage Stress Test (1x, 2x, 3x Friction Ladder)",
        "cmd": [PYTHON_EXE, str(BASE_DIR / "deliverables/phase_7/scripts/test_cost_sensitivity.py")],
        "desc": "Stress tests profitability against 10bps, 20bps, and 30bps execution slippage."
    },
    "10": {
        "title": "Run Rolling Walk-Forward & Out-of-Sample Analysis (IS 2007-15 vs OOS 2016-26)",
        "cmd": [PYTHON_EXE, str(BASE_DIR / "deliverables/phase_7/scripts/test_walk_forward.py")],
        "desc": "Validates strategy stability across in-sample discovery and out-of-sample test eras."
    },
    "11": {
        "title": "Run Macro Regime Historical Stress Test (2008 GFC, 2020 COVID, etc.)",
        "cmd": [PYTHON_EXE, str(BASE_DIR / "deliverables/phase_7/scripts/test_macro_regimes.py")],
        "desc": "Evaluates defensive cash preservation during 6 severe historical market crashes."
    },

    # Analytics & Deep Dive Tools
    "12": {
        "title": "Standalone Market Breadth Deep Dive (% > 200 EMA, Net Highs, Regimes)",
        "cmd": [PYTHON_EXE, str(BASE_DIR / "production/breadth.py")],
        "desc": "Displays detailed trend participation, high proximity, and breadth classification."
    },
    "13": {
        "title": "Standalone JdK Relative Rotation Graph (RRG) Quadrant Analyzer",
        "cmd": [PYTHON_EXE, str(BASE_DIR / "production/plugins/rrg_filter.py")],
        "desc": "Calculates Julius de Kempenaer RS-Ratio and Momentum across 4 quadrants."
    },
    "14": {
        "title": "Standalone Sector Rotation & Relative Strength Matrix",
        "cmd": [PYTHON_EXE, str(BASE_DIR / "production/sector_rotation.py")],
        "desc": "Ranks 12 primary NSE sectors by 1M/3M alpha, internal breadth, and candidate count."
    },
    "15": {
        "title": "Sync Official NSE Sector Taxonomy (Nifty Total Market CSV)",
        "cmd": [PYTHON_EXE, str(BASE_DIR / "production/sync_nse_sectors.py")],
        "desc": "Downloads official Nifty Indices constituent file and maps 1,039 universe stocks."
    },

    # Reports & System Audit
    "16": {
        "title": "View / Regenerate Institutional Interactive HTML Tearsheet (Plotly)",
        "cmd": [PYTHON_EXE, str(BASE_DIR / "scripts/build_institutional_tearsheet.py")],
        "desc": "Compiles standalone HTML tearsheet with equity curves, drawdowns, and monthly returns."
    },
    "17": {
        "title": "Run Master 32-Gate Automated Verification Audit (is_proven engine)",
        "cmd": [PYTHON_EXE, str(BASE_DIR / "deliverables/phase_7/scripts/run_master_proven_gate.py")],
        "desc": "Executes 16-point institutional criteria and outputs 32-gate compliance matrix."
    },
    "18": {
        "title": "Audit & Verify Universe Database Invariants (0 Nulls, 0 Duplicates)",
        "cmd": [PYTHON_EXE, str(BASE_DIR / "scripts/update_universe.py"), "--verify-only"],
        "desc": "Audits nifty500_pit_universe.parquet for zero lookahead, unique keys, and completeness."
    },
}


def clear_screen():
    """Clears terminal screen cleanly across Linux and Windows."""
    if os.name == "nt":
        os.system("cls")
    else:
        sys.stdout.write("\033[H\033[J")
        sys.stdout.flush()


def print_banner():
    """Prints institutional terminal header."""
    sys_tag = "Windows 10/11 (x86_64/ARM64)" if os.name == "nt" else "Samsung Galaxy S23 (PRoot Ubuntu ARM64)"
    print(f"{CYAN}{BOLD}========================================================================================{RESET}")
    print(f"{GREEN}{BOLD}🏛️   PROJECT MIP — INSTITUTIONAL QUANTITATIVE RESEARCH & TRADING DESK{RESET}")
    print(f"{DIM}{sys_tag} | System Engine: {PYTHON_EXE}{RESET}")
    print(f"{CYAN}{BOLD}========================================================================================{RESET}")



def print_menu():
    """Renders the full 18-option categorized workstation menu."""
    print_banner()

    print(f"\n{YELLOW}{BOLD}📡 LIVE PRODUCTION & EXECUTION{RESET}")
    print(f"  {BOLD}[1]{RESET}  🚀 {MENU_ITEMS['1']['title']}")
    print(f"  {BOLD}[2]{RESET}  📱 {MENU_ITEMS['2']['title']}")
    print(f"  {BOLD}[3]{RESET}  ⚡ {MENU_ITEMS['3']['title']}")
    print(f"  {BOLD}[4]{RESET}  💼 {MENU_ITEMS['4']['title']}")
    print(f"  {BOLD}[5]{RESET}  📥 {MENU_ITEMS['5']['title']}")

    print(f"\n{MAGENTA}{BOLD}🔬 STRATEGY BACKTESTING LAB (RUN AS DESIRED){RESET}")
    print(f"  {BOLD}[6]{RESET}  🧪 {MENU_ITEMS['6']['title']}")
    print(f"  {BOLD}[7]{RESET}  🏆 {MENU_ITEMS['7']['title']}")
    print(f"  {BOLD}[8]{RESET}  🎲 {MENU_ITEMS['8']['title']}")
    print(f"  {BOLD}[9]{RESET}  💸 {MENU_ITEMS['9']['title']}")
    print(f"  {BOLD}[10]{RESET} 🔄 {MENU_ITEMS['10']['title']}")
    print(f"  {BOLD}[11]{RESET} 🌪️ {MENU_ITEMS['11']['title']}")

    print(f"\n{BLUE}{BOLD}🧭 ANALYTICS & DEEP DIVE TOOLS{RESET}")
    print(f"  {BOLD}[12]{RESET} 🌐 {MENU_ITEMS['12']['title']}")
    print(f"  {BOLD}[13]{RESET} 🌀 {MENU_ITEMS['13']['title']}")
    print(f"  {BOLD}[14]{RESET} 🏭 {MENU_ITEMS['14']['title']}")
    print(f"  {BOLD}[15]{RESET} 🔄 {MENU_ITEMS['15']['title']}")

    print(f"\n{GREEN}{BOLD}📊 REPORTS & SYSTEM AUDIT{RESET}")
    print(f"  {BOLD}[16]{RESET} 📊 {MENU_ITEMS['16']['title']}")
    print(f"  {BOLD}[17]{RESET} 🛡️ {MENU_ITEMS['17']['title']}")
    print(f"  {BOLD}[18]{RESET} 🔍 {MENU_ITEMS['18']['title']}")

    print(f"\n  {BOLD}[0]{RESET}  🚪 {RED}Exit Workstation{RESET}")
    print(f"{CYAN}{BOLD}========================================================================================{RESET}")


def execute_option(opt: str):
    """Executes the chosen option with streaming output and clean exception trap."""
    if opt not in MENU_ITEMS:
        print(f"\n{RED}Error: Invalid selection '{opt}'. Please enter a number between 0 and 18.{RESET}")
        return

    item = MENU_ITEMS[opt]
    cmd = item["cmd"]

    print("\n" + "=" * 80)
    print(f"{GREEN}{BOLD}EXECUTING OPTION [{opt}]: {item['title']}{RESET}")
    print(f"{DIM}Command: {' '.join(cmd)}{RESET}")
    print("=" * 80 + "\n")

    try:
        # Run subprocess and stream output directly to terminal
        proc = subprocess.run(cmd, cwd=str(BASE_DIR))
        print("\n" + "-" * 80)
        if proc.returncode == 0:
            print(f"{GREEN}{BOLD}✅ Execution completed successfully (Exit Code: 0){RESET}")
        else:
            print(f"{RED}{BOLD}⚠️ Execution finished with non-zero exit code: {proc.returncode}{RESET}")
        print("-" * 80)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️ Execution interrupted by operator (Ctrl+C). Returning to menu...{RESET}")
    except Exception as e:
        print(f"\n{RED}⚠️ Execution error: {e}{RESET}")


def run_interactive_loop():
    """Main terminal loop."""
    while True:
        try:
            clear_screen()
            print_menu()
            choice = input(f"\n{BOLD}Select an option [0-18]: {RESET}").strip()

            if choice in ["0", "q", "quit", "exit"]:
                clear_screen()
                print(f"\n{GREEN}Thank you for using Project MIP Quantitative Workstation. Goodbye!{RESET}\n")
                sys.exit(0)

            if choice in MENU_ITEMS:
                clear_screen()
                execute_option(choice)
                input(f"\n{CYAN}{BOLD}Press ENTER to return to menu...{RESET}")
            else:
                input(f"\n{RED}Invalid option '{choice}'. Press ENTER to try again...{RESET}")
        except KeyboardInterrupt:
            print(f"\n\n{YELLOW}Exiting workstation...{RESET}")
            sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Project MIP Quantitative Workstation")
    parser.add_argument("--option", "-o", type=str, default=None, help="Execute specific option directly (0-18)")
    parser.add_argument("direct_choice", nargs="?", default=None, help="Optional direct option number")

    args = parser.parse_args()
    opt = args.option or args.direct_choice

    if opt is not None:
        if opt in ["0", "q", "quit", "exit"]:
            sys.exit(0)
        execute_option(opt)
    else:
        run_interactive_loop()


if __name__ == "__main__":
    main()
