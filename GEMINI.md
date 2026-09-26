# Workspace Execution Rules: Samsung Galaxy S23 (Termux PRoot Ubuntu)

## 1. Full Environment & Mobile Host Access
- **Authorization**: Antigravity has full, unrestricted access to the entire Android mobile environment and PRoot Linux container.
- **Host Storage Access**:
  - Full read and write access across all shared storage paths: `/sdcard/` and `/storage/emulated/0/` (including `Documents/`, `Download/`, `DCIM/`, `MIP1_Scanner/`, `Need/`, etc.).
  - No artificial path restrictions or folder scanning limits. Read and write wherever required by the user or task.
- **Container & Root Filesystem**:
  - Full root privileges across PRoot Ubuntu (`/`, `/root`, `/usr`, `/etc`, `/var`, `/tmp`, etc.).
- **Termux Utilities**:
  - Termux host binaries in `/data/data/com.termux/files/usr/bin` (e.g. `am`, `pm`, `termux-open`, `termux-wake-lock`, `termux-info`) are available for mobile/device-level operations.

## 2. Python Execution & Architecture Protocol
- Strictly use Ubuntu's system Python (`/usr/bin/python3`) and Ubuntu apt-managed packages.
- Never invoke `/data/data/com.termux/files/usr/bin/python*` or Termux-side site-packages, as Termux has known binary and packaging incompatibilities with many numerical and compiled Python modules.
- Maintain ARM64 Linux PRoot compatibility.
- When loading external pandas pickles (`.pkl`) generated under older or divergent pandas releases, handle `StringArray` serialization cleanly using safe `pickle.Unpickler` subclassing without mutating global library state.
- Prefer Parquet (`pyarrow`) for intermediate and exported datasets.

## 3. Telegram Automated Notifications & Deliverable Dispatch Protocol
- **Bot & Channel**: Integrated with Telegram Bot API (`Crypto_Scan_Afylx_bot`) and User Chat ID (`687480641`).
- **Notification Requirement**:
  - Proactively send Telegram notifications for task starts, milestone updates, verification findings, and completion alerts.
  - Automatically dispatch all gate deliverables (`01_verification.md`, `00_README_INDEX.md`, `SHA256SUMS.txt`, and complete zip bundles) to the user's Telegram using `telegram-notify --gate <name>` or `scripts/telegram_notify.py`.
- **CLI Utility**: `telegram-notify` is installed globally in `/usr/local/bin/telegram-notify`.

## 4. Environment Variables & Secrets Management Protocol
- Authentication tokens are maintained in system environment variables (`/etc/profile.d/02-project-env.sh`, `~/.bashrc`, `/etc/environment`, and `.env`):
  - `GITHUB_TOKEN` / `GH_TOKEN`: GitHub Personal Access Token (classic).
  - `GITHUB_FINE_GRAINED_TOKEN`: GitHub fine-grained PAT.
  - `TELEGRAM_BOT_TOKEN`: Telegram bot token for alerting and execution notifications.
  - `TELEGRAM_CHAT_ID`: Recipient Telegram chat ID.
- Never hardcode raw API tokens into codebase files or scripts. Consume them via `os.environ` or `.env`.
- Never commit `.env` or token files to git (`.gitignore` enforces this).
- In logs and artifact outputs, redact all secret tokens.

## 5. Artifact Export & Version Control Protocol
- Export every generated artifact/report markdown document to the project directory under `artifacts/` (e.g., `/sdcard/Documents/Project MIP/artifacts/`) and `deliverables/`.
- Keep `artifacts/` updated with the latest versions of all verification reports, task lists, and summaries.
- Maintain synchronization with GitHub repository [`Afylx01/MIP`](https://github.com/Afylx01/MIP.git) on branch `main`.
