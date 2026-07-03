#!/usr/bin/env python3
"""Fetch a page via a real headless Chrome browser (undetected-chromedriver).

Fallback for when WebFetch gets a 403 / bot-check page. See SKILL.md.
"""
import argparse
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

try:
    import undetected_chromedriver as uc
    import trafilatura
except ImportError:
    sys.stderr.write(
        "Missing dependencies. Run this once per machine:\n"
        f"  pip install -r {Path(__file__).parent / 'requirements.txt'}\n"
    )
    sys.exit(1)

PROFILE_DIR = Path.home() / ".cache" / "selenium-claude-skill" / "profile"
CONTENT_CHAR_LIMIT = 30000
CHALLENGE_MARKERS = [
    "Just a moment",
    "Checking your browser",
    "cf-browser-verification",
    "Attention Required! | Cloudflare",
    "DDoS protection by",
]


def wait_for_challenge_clear(driver, timeout=20):
    start = time.time()
    while time.time() - start < timeout:
        snippet = driver.page_source[:2000]
        if not any(marker in snippet for marker in CHALLENGE_MARKERS):
            return True
        time.sleep(1)
    return False


def get_status_code(driver):
    status = None
    try:
        logs = driver.get_log("performance")
    except Exception:
        return None
    for entry in logs:
        try:
            msg = json.loads(entry["message"])["message"]
        except Exception:
            continue
        if msg.get("method") == "Network.responseReceived":
            params = msg["params"]
            if params.get("type") == "Document":
                status = params.get("response", {}).get("status", status)
    return status


def detect_chrome_major_version(chrome_bin):
    binary = chrome_bin or shutil.which("google-chrome") or shutil.which("chromium-browser") or shutil.which("chromium")
    if not binary:
        return None
    try:
        out = subprocess.check_output([binary, "--version"], text=True)
    except Exception:
        return None
    match = re.search(r"(\d+)\.", out)
    return int(match.group(1)) if match else None


def fetch(url, headed=False):
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    options = uc.ChromeOptions()
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--window-size=1920,1080")

    chrome_bin = os.environ.get("SELENIUM_SKILL_CHROME_BIN")
    version_main = detect_chrome_major_version(chrome_bin)

    driver = uc.Chrome(
        options=options,
        headless=not headed,
        use_subprocess=True,
        browser_executable_path=chrome_bin,
        version_main=version_main,
    )
    try:
        driver.execute_cdp_cmd("Network.enable", {})
        raw_ua = driver.execute_script("return navigator.userAgent")
        if "Headless" in raw_ua:
            driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": raw_ua.replace("Headless", "")})

        driver.set_page_load_timeout(30)
        try:
            driver.get(url)
        except Exception as e:
            print(f"URL: {url}\nSTATUS: load-error\nERROR: {e}")
            return 1

        wait_for_challenge_clear(driver)

        status = get_status_code(driver)
        final_url = driver.current_url
        title = driver.title
        html = driver.page_source

        content = trafilatura.extract(html, include_comments=False, include_tables=True)
        if not content or len(content.strip()) < 200:
            content = driver.execute_script("return document.body.innerText")

        content = (content or "").strip()
        truncated = len(content) > CONTENT_CHAR_LIMIT
        if truncated:
            content = content[:CONTENT_CHAR_LIMIT]

        print(f"URL: {final_url}")
        print(f"STATUS: {status if status is not None else 'unknown'}")
        print(f"TITLE: {title}")
        print("--- CONTENT ---")
        print(content)
        if truncated:
            print(f"\n[truncated at {CONTENT_CHAR_LIMIT} chars]")
        return 0
    finally:
        driver.quit()


def reset_domain(domain):
    cookie_paths = [
        PROFILE_DIR / "Default" / "Network" / "Cookies",
        PROFILE_DIR / "Default" / "Cookies",
    ]
    found = False
    for path in cookie_paths:
        if not path.exists():
            continue
        found = True
        try:
            conn = sqlite3.connect(str(path))
            cur = conn.cursor()
            cur.execute("DELETE FROM cookies WHERE host_key LIKE ?", (f"%{domain}%",))
            deleted = cur.rowcount
            conn.commit()
            conn.close()
            print(f"Deleted {deleted} cookie(s) matching '{domain}' from {path}")
        except sqlite3.OperationalError as e:
            print(f"Could not open {path}: {e} (is a Chrome process still running from this profile?)")
            return 1
    if not found:
        print("No profile cookie database found yet — nothing to reset.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("url", nargs="?", help="URL to fetch")
    group.add_argument("--reset-domain", metavar="DOMAIN", help="Clear cookies for a domain in the persistent profile")
    parser.add_argument("--headed", action="store_true", help="Run with a visible window (debugging only)")
    args = parser.parse_args()

    if args.reset_domain:
        sys.exit(reset_domain(args.reset_domain))
    else:
        sys.exit(fetch(args.url, headed=args.headed))


if __name__ == "__main__":
    main()
