# Tests for the Untappd Scraper

## Quickstart (offline default)
- Install test deps: `uv sync --group test` (or `pip install -e .[test]`).
- Run offline suite with coverage (skips live scrapes by default):
	- `pytest -m "not webtest" --cov=src --cov-report=xml`
- Run without coverage: `pytest -m "not webtest"`

## Live scraping (opt-in)
- Marked with `webtest`; run with: `pytest -m webtest`.
- Uses the app’s hishel/httpx cache (stored under `.cache/hishel/`) so repeated runs avoid re-downloading.
- To force fresh fetches, delete the cache directory or change the URL/page under test.

## Cache tips
- Default cache path: `.cache/hishel/`
- Clear cache to force fresh responses: `rm -rf .cache/hishel`
- For longer-lived cache during `webtest`, set an env override (tests only):
	- `UNTAPPD_SCRAPER_CACHE_TTL_SECONDS=86400 pytest -m "webtest" --cov=src --cov-report=xml`

## Pre-downloaded HTML fixtures (offline mode)
- The default suite monkeypatches network calls to serve HTML from `tests/html/` via fixtures in tests/conftest.py.
- Current fixture files: `beer.html`, `fridge-list.html`, `user.html`, `userlists.html`, `wishlist.html`, `user-venue-history.html`, `venue_unv.html`, `venue_ver.html`, `venue_ver_activity.html`, `venue_ver_nest.html`, `user-list-1.html`, `user-list-2.html`, `user-beer-history.html`.
- These represent pages such as:
	- https://untappd.com/beer/123456 → tests/html/beer.html
	- https://untappd.com/user/test → tests/html/user.html
	- https://untappd.com/user/test/lists → tests/html/userlists.html
	- https://untappd.com/user/test/lists/201107 → tests/html/fridge-list.html
	- https://untappd.com/user/test/wishlist → tests/html/wishlist.html
	- https://untappd.com/user/test/venues?sort=recent → tests/html/user-venue-history.html
	- https://untappd.com/venue/14705 → tests/html/venue_unv.html
	- https://untappd.com/venue/107565 → tests/html/venue_ver.html
	- https://untappd.com/venue/107565/activity → tests/html/venue_ver_activity.html
	- https://untappd.com/venue/5840988 → tests/html/venue_ver_nest.html

## Refreshing fixture HTML (manual)
1. Pick the fixture file to refresh in `tests/html/`.
2. Fetch the live page and overwrite the file, e.g.:
	 - `curl --compressed https://untappd.com/beer/123456 -o tests/html/beer.html`
	 - `curl --compressed "https://untappd.com/user/test/lists/201107" -o tests/html/fridge-list.html`
3. Re-run tests (`pytest -m "not webtest" --cov=src --cov-report=xml`).

## Markers
- `webtest`: live scraping (hitting untappd.com)
- `httpbin`: reserved for tests that need httpbin (currently unused)
