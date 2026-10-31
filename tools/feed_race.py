"""Which feed sees Pinnacle's line moves first: The Odds API (the bot's feed) or ParlayAPI? Posts nothing and
changes nothing the bot does. On the server, after saving a ParlayAPI key (--set PARLAY_API_KEY=...):

    sudo -u arbbot python3 /opt/arb-bot/tools/feed_race.py [SPORT] [MINUTES] [EVERY_SECONDS]

SPORT defaults to basketball_nba, MINUTES to 30, EVERY_SECONDS to 20. Both feeds are asked for Pinnacle's
moneylines, spreads and totals at the same moment, every EVERY_SECONDS. Each time a Pinnacle price changes, the
time each feed first showed the new price is noted; at the end it prints how many moves each feed had first and
by how many seconds. Credits: about 3 per ask on each feed (30 minutes every 20s: about 270 each; ParlayAPI's free
plan has 1,000 a month)."""
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import arbbot  # noqa: E402

arbbot.load_settings()
sport = sys.argv[1] if len(sys.argv) > 1 else "basketball_nba"
minutes = float(sys.argv[2]) if len(sys.argv) > 2 else 30
every = float(sys.argv[3]) if len(sys.argv) > 3 else 20
FEEDS = {"The Odds API": (os.environ.get("ODDS_API_BASE", "https://api.the-odds-api.com/v4"),
                          os.environ.get("ODDS_API_KEY", "")),
         "ParlayAPI": (os.environ.get("PARLAY_API_BASE", "https://parlay-api.com/v1"),
                       os.environ.get("PARLAY_API_KEY", ""))}
for name, (_, key) in FEEDS.items():
    if not key:
        sys.exit(f"No key for {name}: save it first (--set {'ODDS_API_KEY' if 'Odds' in name else 'PARLAY_API_KEY'}=...).")


def ask(name: str) -> tuple[list, dict]:
    base, key = FEEDS[name]
    q = urllib.parse.urlencode({"apiKey": key, "bookmakers": "pinnacle", "markets": "h2h,spreads,totals",
                                "oddsFormat": "decimal", "dateFormat": "iso"})
    req = urllib.request.Request(f"{base}/sports/{sport}/odds?{q}", headers={"User-Agent": "arbbot-feed-race/1"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read()), {k.lower(): v for k, v in resp.headers.items()}


def prices(events: list) -> dict:
    """{(away, home, start day, market, outcome, point): Pinnacle's price} (games matched by team names, not ids)."""
    out = {}
    for ev in events or []:
        game = (ev.get("away_team", ""), ev.get("home_team", ""), str(ev.get("commence_time", ""))[:10])
        for bm in ev.get("bookmakers", []):
            if bm.get("key") != "pinnacle":
                continue
            for m in bm.get("markets", []):
                for o in m.get("outcomes", []):
                    out[game + (m["key"], o.get("name"), o.get("point"))] = float(o["price"])
    return out


last = {n: {} for n in FEEDS}           # the price each feed showed last
first_seen = {n: {} for n in FEEDS}     # (line, price) -> when this feed first showed it (after its first ask)
started = {n: False for n in FEEDS}
errors = {n: 0 for n in FEEDS}
lines_seen = {n: set() for n in FEEDS}
end = time.time() + minutes * 60
print(f"Racing The Odds API and ParlayAPI on Pinnacle {sport}: every {every:g}s for {minutes:g} minutes...")
with ThreadPoolExecutor(max_workers=2) as pool:
    while time.time() < end:
        tick = time.time()
        futures = {n: pool.submit(ask, n) for n in FEEDS}
        for n, f in futures.items():
            try:
                events, headers = f.result()
            except (urllib.error.URLError, OSError, ValueError) as e:
                errors[n] += 1
                print(f"  ! {n}: {e!r:.120}")
                continue
            now = time.time()
            p = prices(events)
            lines_seen[n] |= set(p)
            for line, price in p.items():
                if started[n] and last[n].get(line) != price:
                    first_seen[n].setdefault((line, price), now)
                last[n][line] = price
            started[n] = True
        time.sleep(max(0.0, every - (time.time() - tick)))

both = set(lines_seen["The Odds API"]) & set(lines_seen["ParlayAPI"])
print(f"\nPinnacle lines: The Odds API {len(lines_seen['The Odds API'])}, ParlayAPI {len(lines_seen['ParlayAPI'])}, "
      f"on both {len(both)}. Failed asks: The Odds API {errors['The Odds API']}, ParlayAPI {errors['ParlayAPI']}.")
moves = set(first_seen["The Odds API"]) | set(first_seen["ParlayAPI"])
lead = []   # seconds ParlayAPI was ahead (negative: behind)
only = {"The Odds API": 0, "ParlayAPI": 0}
for mv in moves:
    a, b = first_seen["The Odds API"].get(mv), first_seen["ParlayAPI"].get(mv)
    if a is not None and b is not None:
        lead.append(a - b)
    elif mv[0] in both:
        only["The Odds API" if a is not None else "ParlayAPI"] += 1
if not lead and not any(only.values()):
    sys.exit("No Pinnacle line moved on both feeds while it ran: try a longer run closer to game time.")
ahead = sum(x > every / 2 for x in lead)
behind = sum(x < -every / 2 for x in lead)
print(f"Moves both feeds showed: {len(lead)}. ParlayAPI first in {ahead}, The Odds API first in {behind}, "
      f"the same ask (within {every / 2:g}s) in {len(lead) - ahead - behind}.")
if lead:
    print(f"ParlayAPI's lead: median {statistics.median(lead):+.0f}s, average {statistics.mean(lead):+.0f}s "
          "(positive = ParlayAPI saw the move sooner).")
print(f"Moves only one feed ever showed: The Odds API {only['The Odds API']}, ParlayAPI {only['ParlayAPI']}.")
