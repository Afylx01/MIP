#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# start_mip.sh — Self-Healing Bootstrapper & One-Click Launcher for Project MIP
# ==============================================================================
# Target: Samsung Galaxy S23 (Termux & PRoot Ubuntu ARM64)
#
# Execution Flow:
#   1. Detects if running inside PRoot Ubuntu or Termux native shell.
#   2. Verifies Android shared storage access (/storage/emulated/0).
#   3. Verifies and installs proot-distro if missing.
#   4. Verifies and installs PRoot Ubuntu rootfs if missing.
#   5. Runs fast dependency probe; installs python3, pip, pandas, numpy, pyarrow,
#      requests, and python-dotenv if missing.
#   6. Ensures ~/.shortcuts/MIP and ~/start.sh exist for Termux:Widget one-tap launch.
#   7. Boots run_mip.py inside PRoot Ubuntu (sub-0.5s execution when installed).
# ==============================================================================

PROJECT_DIR="/storage/emulated/0/Documents/Project MIP"

# 0. Check if already inside PRoot Ubuntu
if [ -f "/etc/issue" ] && grep -qi "ubuntu" /etc/issue; then
    if [ -f "$PROJECT_DIR/run_mip.py" ]; then
        exec /usr/bin/python3 "$PROJECT_DIR/run_mip.py" "$@"
    else
        exec python3 run_mip.py "$@"
    fi
fi

# 1. Verify Android Shared Storage Access
if [ ! -d "$PROJECT_DIR" ]; then
    echo "=================================================================="
    echo "  [MIP] Initializing Android Storage Access..."
    echo "=================================================================="
    if command -v termux-setup-storage >/dev/null 2>&1; then
        termux-setup-storage
        echo "Please tap 'Allow' on the Android permission prompt if prompted."
        for i in 1 2 3 4 5 6 7 8 9 10; do
            if [ -d "$PROJECT_DIR" ]; then break; fi
            sleep 1
        done
    fi

    if [ ! -d "$PROJECT_DIR" ]; then
        echo "[ERROR] Cannot access $PROJECT_DIR."
        echo "Please grant Termux Files/Storage permission in Android Settings -> Apps -> Termux."
        exit 1
    fi
fi

# 2. Check and Install proot-distro
if ! command -v proot-distro >/dev/null 2>&1; then
    echo "=================================================================="
    echo "  [MIP] Installing proot-distro package..."
    echo "=================================================================="
    pkg update -y && pkg install -y proot-distro
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install proot-distro via pkg."
        exit 1
    fi
fi

# 3. Check and Install Ubuntu Rootfs
PREFIX_PATH="${PREFIX:-/data/data/com.termux/files/usr}"
UBUNTU_DIR="$PREFIX_PATH/var/lib/proot-distro/installed-rootfs/ubuntu"

if [ ! -d "$UBUNTU_DIR" ]; then
    echo "=================================================================="
    echo "  [MIP] Installing PRoot Ubuntu Container (One-time setup)..."
    echo "=================================================================="
    proot-distro install ubuntu
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install Ubuntu via proot-distro."
        exit 1
    fi
fi

# 4. Check Ubuntu Python Dependencies (Fast Probe)
NEED_PKG_SETUP=0
if ! proot-distro login ubuntu -- python3 -c "import pandas, pyarrow, numpy, requests, dotenv" >/dev/null 2>&1; then
    NEED_PKG_SETUP=1
fi

if [ $NEED_PKG_SETUP -eq 1 ]; then
    echo "=================================================================="
    echo "  [MIP] Configuring Quantitative Python Environment in Ubuntu..."
    echo "=================================================================="
    proot-distro login ubuntu -- apt update
    proot-distro login ubuntu -- apt install -y python3 python3-pip python3-pandas python3-numpy python3-pyarrow python3-requests python3-dotenv git
    
    # Configure telegram-notify symlink inside Ubuntu
    proot-distro login ubuntu -- ln -sf "$PROJECT_DIR/scripts/telegram_notify.py" /usr/local/bin/telegram-notify
    proot-distro login ubuntu -- chmod +x /usr/local/bin/telegram-notify
fi

# 5. Ensure Termux Home Shortcuts & Termux:Widget Integration
TERMUX_HOME="${HOME:-/data/data/com.termux/files/home}"
if [ -d "$TERMUX_HOME" ]; then
    # Create start.sh shortcut in home
    if [ ! -f "$TERMUX_HOME/start.sh" ]; then
        cat << 'EOF' > "$TERMUX_HOME/start.sh"
#!/data/data/com.termux/files/usr/bin/bash
exec bash "/storage/emulated/0/Documents/Project MIP/start_mip.sh" "$@"
EOF
        chmod +x "$TERMUX_HOME/start.sh"
    fi

    # Create Termux:Widget shortcuts
    mkdir -p "$TERMUX_HOME/.shortcuts"
    mkdir -p "$TERMUX_HOME/.shortcuts/tasks"

    if [ ! -f "$TERMUX_HOME/.shortcuts/MIP" ]; then
        cat << 'EOF' > "$TERMUX_HOME/.shortcuts/MIP"
#!/data/data/com.termux/files/usr/bin/bash
exec bash "/storage/emulated/0/Documents/Project MIP/start_mip.sh" "$@"
EOF
        chmod +x "$TERMUX_HOME/.shortcuts/MIP"
        cp "$TERMUX_HOME/.shortcuts/MIP" "$TERMUX_HOME/.shortcuts/tasks/MIP"
    fi
fi

# 6. Instant Launch into Project MIP Workstation
exec proot-distro login ubuntu \
    --bind /sdcard:/sdcard \
    --bind /storage/emulated/0:/storage/emulated/0 \
    --workdir "$PROJECT_DIR" \
    -- /usr/bin/python3 run_mip.py "$@"
