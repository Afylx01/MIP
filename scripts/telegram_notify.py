#!/usr/bin/env python3
"""
Telegram Notification & Deliverable Dispatcher for Antigravity / Project MIP.
Enables sending real-time progress alerts, status messages, and document deliverables.
"""

import os
import sys
import time
import argparse
import zipfile
from pathlib import Path
import requests

try:
    from dotenv import load_dotenv
    load_dotenv('/sdcard/Documents/Project MIP/.env')
    load_dotenv('/root/.env')
except ImportError:
    pass

def get_credentials():
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        env_file = Path('/etc/environment')
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith('TELEGRAM_BOT_TOKEN='):
                    token = line.split('=', 1)[1].strip('"\'; ')
                elif line.startswith('TELEGRAM_CHAT_ID='):
                    chat_id = line.split('=', 1)[1].strip('"\'; ')

    if not token or not chat_id:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in environment.")

    return token, str(chat_id)

def redact_secrets(text: str) -> str:
    if not text:
        return ""
    try:
        token, _ = get_credentials()
        if token and token in text:
            text = text.replace(token, "[REDACTED_TELEGRAM_TOKEN]")
    except Exception:
        pass
    gh_token = os.environ.get('GITHUB_TOKEN')
    if gh_token and gh_token in text:
        text = text.replace(gh_token, "[REDACTED_GH_TOKEN]")
    pat = os.environ.get('GITHUB_FINE_GRAINED_TOKEN')
    if pat and pat in text:
        text = text.replace(pat, "[REDACTED_PAT]")
    return text

def send_message(text: str, parse_mode: str = None) -> bool:
    """Send text message to Telegram, chunking if necessary."""
    token, chat_id = get_credentials()
    clean_text = redact_secrets(text)
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    chunk_size = 4000
    chunks = [clean_text[i:i + chunk_size] for i in range(0, len(clean_text), chunk_size)]
    success = True

    for chunk in chunks:
        payload = {"chat_id": chat_id, "text": chunk}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code != 200:
                print(f"[Telegram] Error {resp.status_code}: {resp.text}", file=sys.stderr)
                success = False
        except Exception as e:
            print(f"[Telegram] Request exception: {e}", file=sys.stderr)
            success = False
        time.sleep(1.0)

    return success

def send_document(file_path: str, caption: str = None) -> bool:
    """Send a document or artifact directly to the user on Telegram."""
    token, chat_id = get_credentials()
    path = Path(file_path)
    if not path.is_file():
        print(f"[Telegram] File not found: {file_path}", file=sys.stderr)
        return False

    url = f"https://api.telegram.org/bot{token}/sendDocument"
    clean_caption = redact_secrets(caption) if caption else None
    if clean_caption and len(clean_caption) > 1024:
        clean_caption = clean_caption[:1020] + "..."

    try:
        with open(path, "rb") as f:
            files = {"document": (path.name, f)}
            data = {"chat_id": chat_id}
            if clean_caption:
                data["caption"] = clean_caption
            resp = requests.post(url, data=data, files=files, timeout=60)
            if resp.status_code != 200:
                print(f"[Telegram] Error {resp.status_code}: {resp.text}", file=sys.stderr)
                return False
            print(f"[Telegram] Document sent successfully: {path.name}")
            time.sleep(1.5)
            return True
    except Exception as e:
        print(f"[Telegram] Document upload exception: {e}", file=sys.stderr)
        return False

def deliver_gate(gate_name: str, base_dir: str = "/sdcard/Documents/Project MIP") -> bool:
    """Package and dispatch deliverables for a given gate."""
    target_dir = Path(base_dir) / "deliverables" / f"gate_{gate_name}"
    if not target_dir.exists():
        print(f"[Telegram] Gate deliverables directory not found: {target_dir}", file=sys.stderr)
        return False

    send_message(f"🚀 <b>Dispatching Deliverables for Gate {gate_name.upper()}</b>", parse_mode="HTML")
    time.sleep(1.0)

    readme = target_dir / "00_README_INDEX.md"
    verif = target_dir / "01_verification.md"
    sums = target_dir / "SHA256SUMS.txt"

    if verif.exists():
        send_document(str(verif), caption=f"📄 Gate {gate_name.upper()} Verification Report")
    if readme.exists():
        send_document(str(readme), caption=f"📋 Gate {gate_name.upper()} Deliverable Index")
    if sums.exists():
        send_document(str(sums), caption=f"🔒 Gate {gate_name.upper()} SHA-256 Checksums")

    zip_path = Path(base_dir) / "artifacts" / f"gate_{gate_name}_deliverables.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in target_dir.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(target_dir)
                zf.write(file, arcname)

    send_document(str(zip_path), caption=f"📦 Complete Gate {gate_name.upper()} Deliverables Bundle ({zip_path.stat().st_size / 1024:.1f} KB)")
    send_message(f"✅ <b>Gate {gate_name.upper()} Deliverables Dispatched to Telegram</b>", parse_mode="HTML")
    return True

def main():
    parser = argparse.ArgumentParser(description="Telegram notification and deliverable sender")
    parser.add_argument("-m", "--message", type=str, help="Text message to send")
    parser.add_argument("-d", "--document", type=str, help="Path to document file to send")
    parser.add_argument("-c", "--caption", type=str, help="Caption for document")
    parser.add_argument("-g", "--gate", type=str, help="Gate identifier to deliver (e.g. 2c)")
    parser.add_argument("--html", action="store_true", help="Parse text as HTML")

    args = parser.parse_args()

    if args.message:
        send_message(args.message, parse_mode="HTML" if args.html else None)
    if args.document:
        send_document(args.document, caption=args.caption)
    if args.gate:
        deliver_gate(args.gate)

    if not (args.message or args.document or args.gate):
        parser.print_help()

if __name__ == "__main__":
    main()
