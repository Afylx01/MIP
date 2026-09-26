# BUILDER DIRECTIVE: CROSS-PLATFORM PORTABILITY (WINDOWS & LINUX), TERMUX REINSTALL BOOTSTRAPPER & ONE-CLICK LAUNCHER

**Directive ID**: `DIR-PROD-PORTABILITY-01`  
**Standing Gate**: `HALT-14` (Active — Pause for Auditor Review upon task completion)  
**Target Environment**: Dual: Samsung Galaxy S23 (PRoot Ubuntu ARM64) AND Windows 10/11 (x86_64 / ARM64)  
**Workspace**: `/storage/emulated/0/Documents/Project MIP`  
**Deliverables Mirror**: `/sdcard/Documents/deliverables/`  

---

## 1. Executive Objective

Resolve two critical deployment and operational challenges:
1. **Self-Healing Termux Bootstrapper & One-Click Android Launcher (`start_mip.sh`)**:
   If the user uninstalls and reinstalls Termux, PRoot Ubuntu and all apt packages are erased, but shared storage (`/storage/emulated/0/Documents/Project MIP`) remains intact. Create an idempotent launcher script that detects whether PRoot Ubuntu and its packages are installed; if missing, it automatically sets up Termux, installs PRoot Ubuntu, installs all python dependencies, and launches `run_mip.py`; if already installed, it boots in < 0.5s.
2. **Cross-Platform Dual-Environment Compatibility (Linux & Windows)**:
   Ensure the entire project can run seamlessly on both Android/Linux (Termux PRoot) AND Windows (CMD/PowerShell/Git Bash) without manual code modification by dynamically resolving paths, python executables, and terminal commands.

---

## 2. Technical & Architecture Specifications

### Task 1: Self-Healing Termux Bootstrapper (`start_mip.sh`)
- **File**: `/storage/emulated/0/Documents/Project MIP/start_mip.sh` (chmod +x)
- **Execution Flow**:
  1. **Storage Access**: Verify access to `/storage/emulated/0/Documents/Project MIP` (calls `termux-setup-storage` if needed).
  2. **PRoot Ubuntu Check**:
     - Check if `proot-distro` is installed; if not, `pkg update -y && pkg install -y proot-distro`.
     - Check if Ubuntu rootfs exists (`proot-distro list` contains `ubuntu (installed)`); if not, run `proot-distro install ubuntu`.
  3. **Ubuntu Dependencies Check**:
     - Run a probe inside Ubuntu: `python3 -c "import pandas, pyarrow, numpy, requests"`
     - If probe fails, execute inside Ubuntu:
       `apt update && apt install -y python3 python3-pip python3-pandas python3-numpy python3-pyarrow python3-requests python3-dotenv git`
     - Symlink `scripts/telegram_notify.py` to `/usr/local/bin/telegram-notify` inside Ubuntu.
  4. **Idempotency**: If Ubuntu and packages are already present, bypass all checks and launch immediately.
  5. **Launch**: `proot-distro login ubuntu --bind /sdcard:/sdcard --bind /storage/emulated/0:/storage/emulated/0 --workdir "/storage/emulated/0/Documents/Project MIP" -- /usr/bin/python3 run_mip.py "$@"`
  6. **Termux Home & Widget Setup**:
     - Automatically creates a shortcut at `~/.shortcuts/MIP` and `~/start.sh` so the user can launch with 1 tap from Termux:Widget or by typing `./start.sh`.

### Task 2: Cross-Platform Path & Environment Decoupling
Eliminate all hardcoded `/storage/emulated/0/` and `/usr/bin/python3` assumptions across:
- `production/scanner.py`
- `production/breadth.py`
- `production/sector_rotation.py`
- `production/sector_map.py`
- `production/sync_nse_sectors.py`
- `production/telegram_alerts.py`
- `production/run_custom_backtest.py`
- `run_mip.py`
- `scripts/update_universe.py`

**Universal Invariants**:
1. **Dynamic Base Directory (`BASE_DIR`)**:
   ```python
   def get_base_dir() -> Path:
       if "PROJECT_MIP_DIR" in os.environ and Path(os.environ["PROJECT_MIP_DIR"]).exists():
           return Path(os.environ["PROJECT_MIP_DIR"])
       android_path = Path("/storage/emulated/0/Documents/Project MIP")
       if android_path.exists():
           return android_path
       # Fallback: resolve relative to file location
       cur = Path(__file__).resolve()
       return cur.parent.parent if cur.parent.name in ["production", "scripts"] else cur.parent
   ```
2. **Dynamic Python Interpreter (`PYTHON_EXE`)**:
   Use `sys.executable` instead of hardcoded `"/usr/bin/python3"`. This automatically resolves to `python.exe` on Windows and `/usr/bin/python3` on PRoot Ubuntu.
3. **Telegram Dispatch Fallback**:
   In `production/telegram_alerts.py`, check:
   ```python
   TELEGRAM_BIN = Path("/usr/local/bin/telegram-notify")
   if TELEGRAM_BIN.exists() and os.access(str(TELEGRAM_BIN), os.X_OK):
       cmd = [str(TELEGRAM_BIN), "--html", "-m", msg]
   else:
       # Universal python fallback for Windows and environments without global binary
       cmd = [sys.executable, str(BASE_DIR / "scripts/telegram_notify.py"), "--html", "-m", msg]
   ```
4. **Conditional Deliverables Mirroring**:
   If `Path("/sdcard/Documents/deliverables").exists()`, mirror files there; otherwise, mirror to `BASE_DIR / "deliverables"` or skip gracefully.
5. **Cross-Platform Terminal Clear**:
   In `run_mip.py`: `os.system("cls" if os.name == "nt" else "clear")`.

### Task 3: Windows One-Click Batch Launcher (`run_mip.bat`)
- **File**: Root level `/storage/emulated/0/Documents/Project MIP/run_mip.bat`
- Features:
  ```cmd
  @echo off
  title Project MIP — Institutional Momentum Workstation
  cd /d "%~dp0"
  where python >nul 2>nul
  if %errorlevel% neq 0 (
      echo [ERROR] Python not found in system PATH. Please install Python 3.10+ from python.org.
      pause
      exit /b 1
  )
  python -c "import pandas, pyarrow, numpy, requests" >nul 2>nul
  if %errorlevel% neq 0 (
      echo [INFO] Installing required dependencies...
      pip install -r requirements.txt
  )
  python run_mip.py %*
  pause
  ```

### Task 4: Standard `requirements.txt`
- Create `requirements.txt` at project root with:
  ```
  pandas>=2.0.0
  pyarrow>=14.0.0
  numpy>=1.24.0
  requests>=2.28.0
  python-dotenv>=1.0.0
  ```

### Task 5: Runbook Update (`HOW_TO_RUN.md`)
- Add a prominent section: **"One-Click Launcher for Termux (`start_mip.sh`)"** detailing how to launch from Termux or Termux:Widget after an uninstall/reinstall.
- Add a section: **"Running on Windows (`run_mip.bat`)"** detailing how to clone and double-click `run_mip.bat` on Windows 10/11.

---

## 3. Standing Gate HALT-14

Upon completing Tasks 1 through 5:
1. Halt execution and wait for Auditor review.
2. Commit changes cleanly with message `feat(portability): implement self-healing termux bootstrapper, windows batch launcher, and dynamic path resolution`.
3. Report completion for Auditor inspection and certification.
