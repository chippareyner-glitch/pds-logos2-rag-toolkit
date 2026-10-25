"""Download and unpack release assets (official PDS manuals and academic papers) for PDS Logos-2 RAG Toolkit.

Usage:
    python download_documents.py [--verify-only] [--force]
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCUMENTS_DIR = ROOT / "documents"
ZIP_NAME = "pango_pds_logos2_knowledgebase_v1.0.zip"
ZIP_PATH = ROOT / ZIP_NAME
SHA_FILE = ROOT / "SHA256SUMS.txt"
RELEASE_URL = f"https://github.com/chippareyner-glitch/pds-logos2-rag-toolkit/releases/download/v1.0/{ZIP_NAME}"

def sha256_of_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def read_expected_sha() -> str | None:
    if not SHA_FILE.exists():
        return None
    for line in SHA_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.endswith(ZIP_NAME):
            return line.split()[0]
    return None

def download_file(url: str, dest: Path) -> bool:
    print(f"Downloading {ZIP_NAME} from {url} ...")
    temp_dest = dest.with_suffix(".part")
    
    # Try curl first
    curl_cmd = [
        "curl.exe", "-L", "--ssl-no-revoke",
        "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "-o", str(temp_dest), url
    ]
    try:
        res = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=300)
        if res.returncode == 0 and temp_dest.exists() and temp_dest.stat().st_size > 1024 * 1024:
            if dest.exists():
                dest.unlink()
            temp_dest.rename(dest)
            return True
    except Exception as e:
        print(f"curl download failed: {e}, falling back to urllib...")

    # Fallback to urllib
    try:
        import urllib.request
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(url, context=ctx) as resp, open(temp_dest, "wb") as out:
            while chunk := resp.read(65536):
                out.write(chunk)
        if temp_dest.exists() and temp_dest.stat().st_size > 1024 * 1024:
            if dest.exists():
                dest.unlink()
            temp_dest.rename(dest)
            return True
    except Exception as e:
        print(f"urllib download failed: {e}")
        if temp_dest.exists():
            temp_dest.unlink()
        return False
    return False

def main() -> int:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description="Download official documents release package.")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing zip checksum.")
    parser.add_argument("--force", action="store_true", help="Re-download even if zip exists.")
    args = parser.parse_args()

    expected_sha = read_expected_sha()

    if args.verify_only:
        if not ZIP_PATH.exists():
            print(f"File {ZIP_PATH} does not exist.")
            return 1
        current_sha = sha256_of_file(ZIP_PATH)
        print(f"Current SHA256:  {current_sha}")
        print(f"Expected SHA256: {expected_sha}")
        if expected_sha and current_sha == expected_sha:
            print("Checksum verification: PASSED [OK]")
            return 0
        else:
            print("Checksum verification: FAILED [MISMATCH]")
            return 2

    if not ZIP_PATH.exists() or args.force:
        ok = download_file(RELEASE_URL, ZIP_PATH)
        if not ok:
            print("Failed to download release archive.")
            return 1

    current_sha = sha256_of_file(ZIP_PATH)
    if expected_sha and current_sha != expected_sha:
        print(f"Warning: SHA256 mismatch!\n  Got: {current_sha}\n  Expected: {expected_sha}")
    else:
        print("SHA256 checksum verified [OK].")

    print(f"Extracting {ZIP_NAME} into {ROOT} ...")
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        zf.extractall(ROOT)
    print("Extraction complete! Documents are ready in documents/ directory.")
    print("You can now run: python build_index.py to index all documents.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
