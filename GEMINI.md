# Workspace Execution Rules: Samsung Galaxy S23 (Termux PRoot Ubuntu & Pydroid 3)

## 1. Universal Pydroid 3 Coding Protocol (MANDATORY & UNCONDITIONAL)
- **Primary Runtime Target**: All Python code, algorithms, utilities, and workflows written by Antigravity MUST be engineered to run natively and flawlessly inside the **Pydroid 3** Android environment (Python 3.13+ ARM64).
- **Zero-Compiler Invariant**:
  - **STRICTLY FORBIDDEN**: Never introduce or require dependencies that demand C/C++ compilation on Android or lack prebuilt wheels for ARM64 mobile (specifically: `pyarrow`, `fastparquet`, `cython`).
  - **Database & Data Engine**: Always use Python standard library **`sqlite3`** (indexed compound keys: `(date)`, `(symbol, date)`) or compressed CSV/JSON for datasets, universe storage, and caching. Never use Parquet in Pydroid 3 workflows.
- **Allowed Mobile Package Matrix**:
  - Python Standard Library (`sqlite3`, `json`, `math`, `datetime`, `urllib`, `pathlib`, `os`, `sys`, `csv`, `re`, `logging`, `time`).
  - Confirmed Prebuilt Mobile Wheels: `pandas`, `numpy`, `curl_cffi`, `requests`, `matplotlib`, `plotly`, `openpyxl`, `pillow`, `yfinance`, `beautifulsoup4`.
- **Pure-Python Networking & Anti-Bot**:
  - Never call external PRoot Linux CLI binaries (e.g. `/usr/local/bin/telegram-notify`).
  - Use `curl_cffi` (with `impersonate="chrome"`) for anti-bot scraping (NSE Bhavcopy archives, live corporate actions).
  - Use pure-Python HTTP (`requests` or `curl_cffi`) for Telegram alerting, reporting, and file dispatches.
- **Cross-Platform Mobile & Windows Symmetry**:
  - Always resolve paths dynamically using `pathlib.Path(__file__).resolve().parent` or `get_base_dir()`.
  - Code must execute with zero friction and zero code changes across Pydroid 3 (Android) and Windows 10/11.
- **Mobile Execution Optimization**:
  - Pre-index time-series snapshots and rebalance dates into in-memory dictionaries/hash tables for $O(1)$ complexity. Avoid repeating full-DataFrame `.loc` scans inside simulation loops.

## 2. Full Environment & Mobile Host Access
- **Authorization**: Antigravity has full, unrestricted access to the entire Android mobile environment and PRoot Linux container.
- **Host Storage Access**:
  - Full read and write access across all shared storage paths: `/sdcard/` and `/storage/emulated/0/` (including `Documents/`, `Download/`, `DCIM/`, `MIP1_Scanner/`, `Need/`, etc.).
  - No artificial path restrictions or folder scanning limits. Read and write wherever required by the user or task.
- **Container & Root Filesystem**:
  - Full root privileges across PRoot Ubuntu (`/`, `/root`, `/usr`, `/etc`, `/var`, `/tmp`, etc.) for bridge tools, batch exporters, and system maintenance.
- **Termux Utilities**:
  - Termux host binaries in `/data/data/com.termux/files/usr/bin` (e.g. `am`, `pm`, `termux-open`, `termux-wake-lock`, `termux-info`) are available for device-level operations.

## 3. Telegram Automated Notifications Protocol
- **Bot & Channel**: Integrated with Telegram Bot API (`Crypto_Scan_Afylx_bot`) and User Chat ID (`687480641`).
- **Notification Requirement**: Proactively dispatch alerts, tearsheets, and charts via pure-Python Telegram dispatcher.

## 4. Environment Variables & Secrets Management
- Authentication tokens are maintained in system environment variables and `.env`:
  - `GITHUB_TOKEN` / `GH_TOKEN`: GitHub Personal Access Token.
  - `GITHUB_FINE_GRAINED_TOKEN`: GitHub fine-grained PAT.
  - `TELEGRAM_BOT_TOKEN`: Telegram bot token for alerting and execution notifications.
  - `TELEGRAM_CHAT_ID`: Recipient Telegram chat ID.
- Never hardcode raw API tokens into codebase files or scripts. Consume them via `os.environ` or `.env`.
- Never commit `.env` or token files to git.

## 5. Artifact Export & Version Control Protocol
- Export generated artifacts/verification reports to `/sdcard/Documents/deliverables/`.
- Maintain synchronization with GitHub repositories:
  - Main Engine: [`Afylx01/MIP`](https://github.com/Afylx01/MIP.git) on branch `main`.
  - Pydroid 3 Standalone: [`Afylx01/Project_MIP_Pydroid3`](https://github.com/Afylx01/Project_MIP_Pydroid3.git) on branch `main`.
