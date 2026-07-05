#!/usr/bin/env python3
"""
prospect.py — find prospects via Google Places and write them to Supabase
(stage 1a, self-contained port of the miledez-main run.py for the six
IG-makeover segments).

Flow per segment: Places text search per city -> details (phone/website)
-> CNPJ enrichment (site scrape + BrasilAPI) -> insert into prospects.
Dedupe is against the prospects table itself (places_id) — no local cache.

Usage:
  python3 scripts/prospect.py --segment estetica --limit 40
  python3 scripts/prospect.py --all --limit 20      # limit is per segment
  python3 scripts/prospect.py --segment salao --dry-run

Env (read from ../.env if not already set): GOOGLE_PLACES_API_KEY,
SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
"""

import argparse
import os
import re
import sys
import time
import unicodedata

import requests

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (city, uf, tier) — tier 1 capital, 2 interior grande, 3 interior
CITIES = [
    ("Sao Paulo", "SP", 1),
    ("Rio de Janeiro", "RJ", 1),
    ("Curitiba", "PR", 1),
    ("Belo Horizonte", "MG", 1),
]
RESULTS_PER_CITY = 40

COMMON_EXCLUDES = [
    "distribuidora", "atacado", "fornecedor",
    "curso", "treinamento", "capacitacao", "escola tecnica",
    "software", "sistema", "plataforma",
    "consultoria", "assessoria", "franquia master",
]

SEGMENTS = {
    "estetica": {
        "queries": ["clínica de estética", "estética facial e corporal",
                    "clínica de harmonização facial"],
        "excludes": ["equipamentos", "aparelhos esteticos"],
    },
    "odonto": {
        "queries": ["clínica odontológica", "consultório dentista",
                    "odontologia estética lentes"],
        "excludes": ["protese dentaria laboratorio", "dental atacado"],
    },
    "salao": {
        "queries": ["salão de beleza", "barbearia",
                    "studio de sobrancelhas e cílios"],
        "excludes": ["cosmeticos atacado", "produtos para salao"],
    },
    "restaurante": {
        "queries": ["restaurante", "pizzaria", "hamburgueria artesanal"],
        "excludes": ["dark kitchen", "food service atacado"],
    },
    "pet": {
        "queries": ["pet shop", "clínica veterinária", "banho e tosa"],
        "excludes": ["racao atacado", "pet shop online"],
    },
    "fitness": {
        "queries": ["academia de musculação", "studio de pilates",
                    "box de crossfit"],
        "excludes": ["equipamentos fitness", "suplementos loja"],
    },
}

CNPJ_RE = re.compile(r"\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[-\s]?\d{2}")
UA = {"User-Agent": "Mozilla/5.0 (compatible; mildez-prospector/1.0)"}
TIMEOUT = 10


def load_env() -> None:
    path = os.path.join(REPO_ROOT, ".env")
    if not os.path.isfile(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            if not os.environ.get(key.strip()):
                os.environ[key.strip()] = value


# ── Places ──────────────────────────────────────────────────────────

def places_text_search(query: str, api_key: str) -> dict:
    resp = requests.get(
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        params={"query": query, "key": api_key, "language": "pt-BR"},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def place_details(place_id: str, api_key: str) -> dict:
    resp = requests.get(
        "https://maps.googleapis.com/maps/api/place/details/json",
        params={
            "place_id": place_id,
            "fields": "name,formatted_address,formatted_phone_number,website,business_status",
            "key": api_key,
            "language": "pt-BR",
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json().get("result", {})


def _fold(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(c) != "Mn"
    )


def is_excluded(name: str, excludes: list[str]) -> bool:
    folded = _fold(name)
    return any(_fold(kw) in folded for kw in excludes)


# ── CNPJ enrichment ─────────────────────────────────────────────────

def cnpj_from_website(url: str) -> str | None:
    if not url:
        return None
    try:
        resp = requests.get(url, headers=UA, timeout=8, allow_redirects=True)
        for raw in CNPJ_RE.findall(resp.text):
            digits = re.sub(r"\D", "", raw)
            if len(digits) == 14:
                return digits
    except requests.RequestException:
        pass
    return None


def format_cnpj(digits: str) -> str:
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


# ── Row mapping ─────────────────────────────────────────────────────

def phone_e164(raw: str) -> str | None:
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("55") and len(digits) in (12, 13):
        return "+" + digits
    if len(digits) in (10, 11):
        return "+55" + digits
    return None


def build_row(details: dict, place_id: str, segment: str,
              city: str, uf: str, tier: int) -> dict | None:
    name = (details.get("name") or "").strip()
    if not name or details.get("business_status") == "CLOSED_PERMANENTLY":
        return None
    website = (details.get("website") or "").strip() or None
    cnpj_digits = cnpj_from_website(website)
    return {
        "business_name": name,
        "segment": segment,
        "cnpj": format_cnpj(cnpj_digits) if cnpj_digits else None,
        "city": city,
        "uf": uf,
        "city_tier": tier,
        "phone_e164": phone_e164(details.get("formatted_phone_number")),
        "website": website,
        "places_id": place_id,
    }


# ── Segment run ─────────────────────────────────────────────────────

def run_segment(db, segment: str, api_key: str, limit: int | None,
                dry_run: bool) -> int:
    cfg = SEGMENTS[segment]
    excludes = COMMON_EXCLUDES + cfg["excludes"]

    existing_places = {
        r["places_id"]
        for r in db.table("prospects").select("places_id")
        .not_.is_("places_id", "null").execute().data
    }
    existing_cnpjs = {
        r["cnpj"]
        for r in db.table("prospects").select("cnpj")
        .not_.is_("cnpj", "null").execute().data
    }

    rows = []
    print(f"\n[{segment}]")
    for city, uf, tier in CITIES:
        cap = RESULTS_PER_CITY if limit is None else limit - len(rows)
        if cap <= 0:
            break
        found_in_city = 0
        for query in cfg["queries"]:
            if len(rows) >= (limit or RESULTS_PER_CITY * len(CITIES)):
                break
            try:
                data = places_text_search(f"{query} {city} Brasil", api_key)
            except requests.RequestException as e:
                print(f"  WARNING: search failed ({query}, {city}): {e}")
                continue
            if data.get("status") not in ("OK", "ZERO_RESULTS"):
                print(f"  WARNING: Places status={data.get('status')} ({city})")
                continue
            for place in data.get("results", []):
                if len(rows) >= (limit or RESULTS_PER_CITY * len(CITIES)):
                    break
                pid = place.get("place_id")
                if not pid or pid in existing_places:
                    continue
                existing_places.add(pid)
                if is_excluded(place.get("name", ""), excludes):
                    continue
                time.sleep(0.15)
                try:
                    details = place_details(pid, api_key)
                except requests.RequestException:
                    details = {}
                row = build_row({**place, **details}, pid, segment, city, uf, tier)
                if row is None:
                    continue
                if row["cnpj"] and row["cnpj"] in existing_cnpjs:
                    row["cnpj"] = None  # same CNPJ across branches
                if row["cnpj"]:
                    existing_cnpjs.add(row["cnpj"])
                rows.append(row)
                found_in_city += 1
                print(f"  + {row['business_name'][:50]} ({city})")
            time.sleep(0.4)
        print(f"  -> {found_in_city} new in {city}")

    if rows and not dry_run:
        db.table("prospects").insert(rows).execute()
    with_site = sum(1 for r in rows if r["website"])
    with_cnpj = sum(1 for r in rows if r["cnpj"])
    print(f"  {segment}: {len(rows)} new ({with_site} with website, "
          f"{with_cnpj} with CNPJ)" + (" [dry-run]" if dry_run else ""))
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--segment", choices=sorted(SEGMENTS))
    group.add_argument("--all", action="store_true", help="run all six segments")
    parser.add_argument("--limit", type=int, default=None,
                        help="max new prospects per segment")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_env()
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    missing = [n for n, v in [("GOOGLE_PLACES_API_KEY", api_key),
                              ("SUPABASE_URL", supabase_url),
                              ("SUPABASE_SERVICE_ROLE_KEY", supabase_key)] if not v]
    if missing:
        print(f"error: missing env vars: {', '.join(missing)}", file=sys.stderr)
        return 1

    from supabase import create_client
    db = create_client(supabase_url, supabase_key)

    targets = sorted(SEGMENTS) if args.all else [args.segment]
    total = sum(run_segment(db, s, api_key, args.limit, args.dry_run)
                for s in targets)
    print(f"\ntotal new prospects: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
