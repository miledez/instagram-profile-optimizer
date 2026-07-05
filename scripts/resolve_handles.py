#!/usr/bin/env python3
"""
resolve_handles.py — resolve Instagram handles for prospects (stage 1b, step 1).

Strategy (in order, stop at first hit):
  1. website_scrape — fetch prospect.website, regex instagram.com/{handle}
     links (also check linktree/beacons pages one level deep).
  2. search        — Places details 'url'/'website' variants; if none,
     queue for manual (NO Google scraping — ToS).
  3. manual        — dashboard queue, human pastes handle.

Writes back to Supabase prospects.ig_handle + ig_resolution_method.
Validation: handle regex ^[A-Za-z0-9._]{1,30}$; dedupe against existing
handles; skip if in suppression_list.

Usage:
  python resolve_handles.py --limit 100 [--dry-run]

Env: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

TODO(week1): implement. Keep pure functions testable:
  extract_ig_handles(html: str) -> list[str]
  pick_best_handle(handles: list[str], business_name: str) -> str | None
"""

import re

IG_LINK_RE = re.compile(
    r"instagram\.com/([A-Za-z0-9._]{1,30})/?(?:[\"'?#/]|$)", re.IGNORECASE
)
IGNORED_HANDLES = {"p", "reel", "reels", "stories", "explore", "accounts", "sharer"}


def extract_ig_handles(html: str) -> list[str]:
    """All candidate handles found in a page, order-preserving, deduped."""
    seen, out = set(), []
    for m in IG_LINK_RE.finditer(html):
        h = m.group(1).lower().rstrip(".")
        if h not in seen and h not in IGNORED_HANDLES:
            seen.add(h)
            out.append(h)
    return out


def pick_best_handle(handles: list[str], business_name: str) -> str | None:
    """Prefer handle with highest token overlap with business name."""
    if not handles:
        return None
    tokens = set(re.sub(r"[^a-z0-9]", "", w) for w in business_name.lower().split())
    def score(h: str) -> int:
        clean = re.sub(r"[^a-z0-9]", "", h)
        return sum(1 for t in tokens if t and t in clean)
    return max(handles, key=score)


if __name__ == "__main__":
    raise SystemExit("TODO: wire Supabase + fetch loop (see docstring).")
