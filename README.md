# claude-selenium-fetch

A Claude Code skill that fetches web pages through a stealth-patched
headless Chrome (via `undetected-chromedriver`) when `WebFetch` gets
blocked — 403s, Cloudflare/PerimeterX "checking your browser" pages, or
other bot detection.

## What it does

- Fetch-only: loads a URL, waits for bot challenges to clear, extracts
  content. No clicking or form-filling.
- Persistent per-machine browser profile, so a solved bot challenge
  stays solved on later fetches instead of re-challenging every time.
- Hybrid content extraction — clean article text via `trafilatura`,
  falling back to rendered visible text on non-article pages.
- Real HTTP status captured via the Chrome DevTools protocol.

Does **not** help with geo-blocking or content behind a login.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Requires Chrome or Chromium installed.

## Usage

```bash
.venv/bin/python fetch.py "https://example.com/some-page"
.venv/bin/python fetch.py --reset-domain example.com   # clear a stuck domain's cookies
```

Concurrent calls share one browser profile and serialize through a file
lock — a second call waits rather than racing the first.

## Tests

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest
```

Covers the pure logic (challenge detection, status-code parsing,
cookie reset) with no live browser needed. Actual browser/network
behavior is verified manually — see `SKILL.md`.

See `SKILL.md` for full details and how this registers as a Claude Code
skill.

## License

MIT — see [LICENSE](LICENSE).
