#!/usr/bin/env python3
"""
resolve_handles.py — resolve Instagram handles for prospects (stage 1b, step 1).

Strategy (in order, stop at first hit):
  1. website_scrape — fetch prospect.website, regex instagram.com/{handle}
     links (also check linktree/beacons pages one level deep).
  2. search        — Places details 'website' (needs GOOGLE_PLACES_API_KEY);
     if none, queue for manual (NO Google scraping — ToS).
  3. manual        — dashboard queue, human pastes handle (row left null).

Writes back to Supabase prospects.ig_handle + ig_resolution_method.
Validation: handle regex ^[A-Za-z0-9._]{1,30}$; dedupe against existing
handles; skip if in suppression_list.

Usage:
  python resolve_handles.py --limit 100 [--dry-run]

Env: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, GOOGLE_PLACES_API_KEY (optional)
"""

import argparse
import os
import re
import sys
import time
from urllib.parse import urljoin, urlparse

import requests

# \\? handles JSON-escaped URLs (instagram.com\/handle) in linktree/SPA payloads
IG_LINK_RE = re.compile(
    r"instagram\.com\\?/([A-Za-z0-9._]{1,30})\\?/?(?:[\"'?#/\\]|$)", re.IGNORECASE
)
HANDLE_RE = re.compile(r"^[A-Za-z0-9._]{1,30}$")
IGNORED_HANDLES = {
    # IG paths that are not profiles
    "p", "reel", "reels", "stories", "explore", "accounts", "sharer",
    "share", "tv", "direct", "invites", "about", "legal", "developer",
    "blog", "web", "embed",
    # official platform accounts sites link to (never a prospect)
    "whatsapp", "facebook", "instagram", "meta", "twitter", "youtube",
    "linkedin", "tiktok",
}

AGGREGATOR_DOMAINS = (
    "linktr.ee", "beacons.ai", "bio.link", "linkin.bio",
    "taplink.cc", "campsite.bio", "lnk.bio", "biolinky.co",
)
HREF_RE = re.compile(r"href=[\"']([^\"']+)[\"']", re.IGNORECASE)

UA = "Mozilla/5.0 (X11; Linux x86_64) mildez-resolver/1.0"
TIMEOUT = 10
MAX_AGGREGATOR_FOLLOWS = 2
FETCH_DELAY_S = 0.5


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


def handle_from_instagram_url(url: str) -> str | None:
    """If the URL itself is an instagram.com profile link, return its handle."""
    m = IG_LINK_RE.search(url + "/")
    if m:
        h = m.group(1).lower().rstrip(".")
        if h not in IGNORED_HANDLES:
            return h
    return None


def extract_aggregator_links(html: str, base_url: str) -> list[str]:
    """Absolute URLs in the page pointing at link-in-bio aggregators."""
    seen, out = set(), []
    for href in HREF_RE.findall(html):
        absolute = urljoin(base_url, href)
        host = urlparse(absolute).netloc.lower().removeprefix("www.")
        if any(host == d or host.endswith("." + d) for d in AGGREGATOR_DOMAINS):
            if absolute not in seen:
                seen.add(absolute)
                out.append(absolute)
    return out


def normalize_url(url: str) -> str:
    return url if url.startswith(("http://", "https://")) else "https://" + url


def fetch_html(url: str, verify: bool = True) -> str:
    try:
        resp = requests.get(
            normalize_url(url), timeout=TIMEOUT,
            headers={"User-Agent": UA}, allow_redirects=True, verify=verify,
        )
        if resp.ok and "text/html" in resp.headers.get("content-type", "text/html"):
            return resp.text[:500_000]
    except requests.exceptions.SSLError:
        # local-SMB sites with broken certs; public read-only fetch
        if verify:
            return fetch_html(url, verify=False)
    except requests.RequestException:
        pass
    return ""


def resolve_via_website(website: str, business_name: str) -> str | None:
    direct = handle_from_instagram_url(website)
    if direct:
        return direct

    html = fetch_html(website)
    if not html:
        return None

    handles = extract_ig_handles(html)
    if not handles:
        for link in extract_aggregator_links(html, normalize_url(website))[:MAX_AGGREGATOR_FOLLOWS]:
            time.sleep(FETCH_DELAY_S)
            handles = extract_ig_handles(fetch_html(link))
            if handles:
                break
    return pick_best_handle(handles, business_name)


def places_website(places_id: str, api_key: str) -> str | None:
    try:
        resp = requests.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={"place_id": places_id, "fields": "website", "key": api_key},
            timeout=TIMEOUT,
        )
        return resp.json().get("result", {}).get("website") or None
    except (requests.RequestException, ValueError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_key:
        print("error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required", file=sys.stderr)
        return 1
    places_key = os.environ.get("GOOGLE_PLACES_API_KEY")

    from supabase import create_client
    db = create_client(supabase_url, supabase_key)

    prospects = (
        db.table("prospects")
        .select("id,business_name,website,places_id")
        .is_("ig_handle", "null")
        .order("created_at")
        .limit(args.limit)
        .execute()
        .data
    )
    if not prospects:
        print("no prospects pending resolution")
        return 0

    suppressed = {
        r["ig_handle"].lower()
        for r in db.table("suppression_list").select("ig_handle").not_.is_("ig_handle", "null").execute().data
    }
    taken = {
        r["ig_handle"].lower()
        for r in db.table("prospects").select("ig_handle").not_.is_("ig_handle", "null").execute().data
    }

    stats = {"website_scrape": 0, "search": 0, "manual": 0, "suppressed": 0, "duplicate": 0}

    for p in prospects:
        handle, method = None, None

        if p.get("website"):
            handle = resolve_via_website(p["website"], p["business_name"])
            method = "website_scrape"
        if not handle and places_key and p.get("places_id"):
            site = places_website(p["places_id"], places_key)
            if site:
                handle = resolve_via_website(site, p["business_name"])
                method = "search"

        if not handle or not HANDLE_RE.match(handle):
            stats["manual"] += 1
            print(f"  manual   {p['business_name']}")
            continue
        if handle in suppressed:
            stats["suppressed"] += 1
            print(f"  suppress {p['business_name']} -> @{handle}")
            continue
        if handle in taken:
            stats["duplicate"] += 1
            print(f"  dupe     {p['business_name']} -> @{handle} (already assigned)")
            continue

        taken.add(handle)
        stats[method] += 1
        print(f"  {method:<8} {p['business_name']} -> @{handle}")
        if not args.dry_run:
            db.table("prospects").update(
                {"ig_handle": handle, "ig_resolution_method": method}
            ).eq("id", p["id"]).execute()
        time.sleep(FETCH_DELAY_S)

    total = len(prospects)
    resolved = stats["website_scrape"] + stats["search"]
    print(
        f"\nresolved {resolved}/{total} ({100 * resolved // total}%) — "
        f"website_scrape={stats['website_scrape']} search={stats['search']} "
        f"manual={stats['manual']} suppressed={stats['suppressed']} "
        f"duplicate={stats['duplicate']}"
        + (" [dry-run, nothing written]" if args.dry_run else "")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
