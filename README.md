# claude-selenium-fetch

[![Tests](https://github.com/malako/claude-selenium-fetch/actions/workflows/test.yml/badge.svg)](https://github.com/malako/claude-selenium-fetch/actions/workflows/test.yml)

A Claude Code skill that fetches web pages through a stealth-patched
headless Chrome (via `undetected-chromedriver`) for two cases `WebFetch`
can't handle:

1. **Anti-bot blocking** — 403s, Cloudflare/PerimeterX "checking your
   browser" pages, or other bot detection.
2. **JavaScript-rendered pages** — WebFetch returns empty/truncated/shell
   content because the page is built client-side (SPAs, Swagger/ReDoc API
   docs, dashboards). A real browser runs the JS, so the real content
   appears.

## What it does

- Fetch-only: loads a URL, waits for JS/bot challenges to clear, extracts
  content. No clicking or form-filling.
- Persistent per-machine browser profile, so a solved bot challenge
  stays solved on later fetches instead of re-challenging every time.
- Hybrid content extraction — clean article text via `trafilatura`,
  falling back to rendered visible text on non-article pages (SPAs,
  dashboards).
- Real HTTP status captured via the Chrome DevTools protocol.

Does **not** help with geo-blocking or content behind a login.

## Install

```bash
git clone https://github.com/malako/claude-selenium-fetch.git
cd claude-selenium-fetch
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Requires Chrome or Chromium installed.

To register it as a Claude Code skill (available in every project, not
just this directory):

```bash
ln -s "$(pwd)" ~/.claude/skills/claude-selenium-fetch
```

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
