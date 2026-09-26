#!/usr/bin/env python3
"""
Step 2 — Gate 0 Restatement
Extracts relevant lines from cached circular PDF and rebalancing schedule HTML,
demonstrating bulletin contents and formally restating Gate 0 findings.
"""
import os
import re
import zlib

PDF_FILE = "data/raw_bulletins/nifty_replacement_circular_sep_2020.pdf"
HTML_FILE = "data/raw_bulletins/niftyindices___rebalancing_schedule_200.html"

def extract_pdf_lines(pdf_path):
    with open(pdf_path, "rb") as f:
        data = f.read()
    streams = re.findall(rb'stream[\r\n]+(.*?)[\r\n]+endstream', data, re.DOTALL)
    extracted = []
    for s in streams:
        try:
            d = zlib.decompress(s)
            tj_blocks = re.findall(rb'\[(.*?)\]\s*TJ', d)
            for b in tj_blocks:
                b_chars = re.findall(rb'\((.*?)\)', b)
                b_text = ''.join(c.decode('latin1', errors='ignore') for c in b_chars).strip()
                if b_text and len(b_text) > 3:
                    extracted.append(b_text)
        except:
            pass
    return extracted

def extract_html_lines(html_path):
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()
    clean = re.sub(r"<style.*?</style>", "", html, flags=re.DOTALL)
    clean = re.sub(r"<script.*?</script>", "", clean, flags=re.DOTALL)
    clean = re.sub(r"<[^>]+>", "\n", clean)
    lines = [l.strip() for l in clean.splitlines() if l.strip()]
    return lines

def main():
    print("=" * 80)
    print("STEP 2: GATE 0 RESTATEMENT — BULLETIN & REBALANCING SCHEDULE EXTRACTION")
    print("=" * 80)

    print("\n--- 1. Extraction from nifty_replacement_circular_sep_2020.pdf ---")
    pdf_lines = extract_pdf_lines(PDF_FILE)
    print(f"Total lines extracted from PDF stream objects: {len(pdf_lines)}")
    print("Sample lines (Header & Circular metadata):")
    for idx, l in enumerate(pdf_lines[:20], 1):
        print(f"  [PDF-{idx:02d}] {l}")

    print("\n--- 2. Extraction from niftyindices___rebalancing_schedule_200.html ---")
    html_lines = extract_html_lines(HTML_FILE)
    print(f"Total lines extracted from HTML text: {len(html_lines)}")
    # Find section on rebalancing schedule
    rebal_lines = []
    keywords = ["reconstitution", "rebalancing", "cutoff", "semi-annually", "effective date", "nifty 500", "nifty 50"]
    for l in html_lines:
        if any(k in l.lower() for k in keywords) and len(l) > 10:
            if l not in rebal_lines:
                rebal_lines.append(l)

    print("Sample lines (Rebalancing Schedule / Index Calendar):")
    for idx, l in enumerate(rebal_lines[:20], 1):
        print(f"  [HTML-{idx:02d}] {l}")

    print("\n" + "=" * 80)
    print("GATE 0 FINDING RESTATEMENT:")
    print("  The 404s encountered in Gate 0 were directory listings, not individual bulletins.")
    print("  post-2020-09 bulletin availability NOT ESTABLISHED; deferred to Phase 5.6.")
    print("  (Do not parse bulletins into events at this stage.)")
    print("=" * 80)

if __name__ == "__main__":
    main()
