---
name: claude-selenium-fetch
description: Fetch a web page with a real headless Chrome browser (undetected-chromedriver) for two cases WebFetch can't handle. (1) Anti-bot blocking — a 403, a bot-check/"Just a moment" page, or Cloudflare/PerimeterX challenges. (2) JavaScript-rendered pages where WebFetch comes back empty, truncated, or as a shell because the content is built client-side (single-page apps, Swagger/ReDoc/other API docs, dashboards). It renders the page, waits for the JS to settle, and extracts the resulting text. Maintains a persistent per-machine browser profile so bot-challenge cookies persist across fetches instead of re-triggering the challenge every time. Use as a fallback after WebFetch fails OR returns unusable/empty content — not as a first choice, since it's much slower. Fetch-only, not interactive (no clicking/form-filling). Does NOT help with geo-blocking or content behind a login.
---

# Claude Selenium Fetch

Fallback fetcher for pages a normal HTTP fetch can't get past. Renders the
page in a real (headless) Chrome via `undetected-chromedriver`, which
defeats most headless-browser fingerprinting checks that trigger 403s.

## When to use

As a fallback after `WebFetch` has already failed **or returned unusable
content**, in either of these cases:

- **Anti-bot blocking** — a 403, a Cloudflare/PerimeterX "checking your
  browser" page, or content that's clearly a bot-challenge shell rather
  than the real page.
- **JavaScript-rendered pages** — WebFetch returns empty, truncated, or
  an obvious shell because the page builds its content client-side (SPAs,
  Swagger/ReDoc API docs, dashboards, admin UIs). WebFetch doesn't run
  JS; a real browser does, so the actual content appears. If WebFetch
  gives you a near-empty page or a small model's vague paraphrase of a
  docs site, this is the fix.

Don't use this as a first attempt; it launches a real browser and is
much slower than WebFetch.

This is a **fetch-only** tool: it loads the URL, waits for JS/bot
challenges to settle, and extracts the resulting text. It does not
click, fill forms, or otherwise interact with the page.

It will **not** help if the failure is actually geo-blocking or a login
wall — those aren't bot-detection problems and a browser alone doesn't
solve them.

## One-time setup (per machine)

```bash
cd <this skill's directory>
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Requires Chrome (or Chromium) installed. `undetected-chromedriver` finds
it automatically; if it's in a nonstandard location, set
`SELENIUM_SKILL_CHROME_BIN=/path/to/chrome`.

`requirements.txt` also pins `setuptools` — `undetected-chromedriver`
imports `distutils`, which was removed from the stdlib in Python 3.12+;
`setuptools` provides a shim. Without it, `fetch.py` fails at import
with a clear error telling you to run the install command above.

## Usage

Always invoke via the venv's interpreter, not bare `python3` — the
dependencies only exist there:

```bash
.venv/bin/python fetch.py "https://example.com/some-page"
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
.venv/bin/python fetch.py --reset-domain example.com
.venv/bin/python fetch.py "https://example.com/some-page"
```

This is **not** automatic — nothing resets on its own. Resetting one
domain doesn't touch cookies/sessions for any other domain in the shared
profile.

## Concurrent fetches

All fetches and resets share one browser profile, so calls serialize
through a file lock (`~/.cache/selenium-claude-skill/.lock`) — a second
concurrent invocation waits for the first to finish rather than racing
it or crashing. If you fire off several fetches at once, expect them to
run one at a time, not in parallel.

## Debugging

`--headed` runs with a visible browser window instead of headless, for
watching what's actually happening on a page that's still failing. Not
for normal use.
