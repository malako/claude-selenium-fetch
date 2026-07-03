---
name: selenium-fetch
description: Fetch a web page with a real headless Chrome browser (undetected-chromedriver) when WebFetch fails with a 403, a bot-check/"Just a moment" page, or other anti-bot blocking (Cloudflare, PerimeterX, etc.). Maintains a persistent per-machine browser profile so bot-challenge cookies persist across fetches instead of re-triggering the challenge every time. Use this as a fallback after WebFetch fails — not as a first choice, since it's much slower. Does NOT help with geo-blocking or content behind a login.
---

# Selenium Fetch

Fallback fetcher for pages a normal HTTP fetch can't get past. Renders the
page in a real (headless) Chrome via `undetected-chromedriver`, which
defeats most headless-browser fingerprinting checks that trigger 403s.

## When to use

Only after `WebFetch` has already failed on a URL — with a 403, a
Cloudflare/PerimeterX "checking your browser" page, or content that's
clearly a bot-challenge shell rather than the real page. Don't use this
as a first attempt; it launches a real browser and is much slower than
WebFetch.

It will **not** help if the failure is actually geo-blocking or a login
wall — those aren't bot-detection problems and a browser alone doesn't
solve them.

## One-time setup (per machine)

```bash
pip install -r requirements.txt
```

(Or into a venv if you prefer — `fetch.py` just needs `selenium`,
`undetected-chromedriver`, and `trafilatura` importable.)

Requires Chrome (or Chromium) installed. `undetected-chromedriver` finds
it automatically; if it's in a nonstandard location, set
`SELENIUM_SKILL_CHROME_BIN=/path/to/chrome`.

## Usage

Fetch a URL:

```bash
python3 fetch.py "https://example.com/some-page"
```

Output:

```
URL: <final URL after redirects>
STATUS: <real HTTP status of the main document, captured via CDP>
TITLE: <page title>
--- CONTENT ---
<extracted page content>
```

Content extraction is hybrid: tries `trafilatura` (clean article-style
text) first; if that returns little/nothing (common on non-article pages
— SPAs, dashboards, forum threads), falls back to the page's rendered
visible text (`document.body.innerText`). Content is capped at 30,000
characters.

## If a domain keeps failing

The browser profile at `~/.cache/selenium-claude-skill/profile` persists
across runs (that's what lets a solved Cloudflare challenge stay solved
on the next fetch instead of re-challenging every time). If a specific
domain keeps failing even through this skill, its cookies for that
domain may be stale/flagged. Clear just that domain and retry once:

```bash
python3 fetch.py --reset-domain example.com
python3 fetch.py "https://example.com/some-page"
```

This is **not** automatic — nothing resets on its own. Resetting one
domain doesn't touch cookies/sessions for any other domain in the shared
profile.

## Debugging

`--headed` runs with a visible browser window instead of headless, for
watching what's actually happening on a page that's still failing. Not
for normal use.
