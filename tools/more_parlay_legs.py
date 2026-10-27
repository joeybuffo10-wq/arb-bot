"""Did the more parlays (#more-parlays) keep any bet from going out as a single? Run it on the server:

    sudo -u arbbot python3 /opt/arb-bot/tools/more_parlay_legs.py

Lists every leg of every posted more parlay and whether the same bet (any book) was also alerted on its own, in the
+EV or outlier log. A parlay never holds a single back: a leg that isn't one didn't clear the single bars."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import arbbot  # noqa: E402

arbbot.load_settings()
cfg = arbbot.Config.from_env()
rows = arbbot._read_csv(cfg.more_parlay_log_file) if cfg.more_parlay_log_file else []
if not rows:
    sys.exit("No more parlays logged.")


def lid(r):
    return arbbot.leg_id(r.get("event_id"), r.get("market"), r.get("player"), r.get("outcome"), r.get("point"))


singles = {}
for name in (cfg.ev_log_file, cfg.outlier_log_file):
    for r in arbbot._read_csv(name) if name else []:
        singles.setdefault(lid(r), r)

legs = both = 0
for r in rows:
    print(f"\n{r['first_seen'][:16]}  {r['book']}  {r['legs']}")
    for leg in arbbot.parlay_legs(r):
        legs += 1
        s = singles.get(lid(leg))
        both += bool(s)
        what = " ".join(str(x) for x in (leg.get("player"), leg.get("outcome"), leg.get("point"),
                                         arbbot.MARKET_NAMES.get(leg["market"], leg["market"])) if x not in ("", None))
        print(f"  {'✅ also a single' if s else '·  not a single'}  {what[:60]}"
              + (f"  ({s['book']} {float(s['best_ev_pct']):+.1f}% EV, {s['first_seen'][11:16]})" if s else ""))
print(f"\n{len(rows)} more parlays, {legs} legs: {both} also went out as singles, {legs - both} never cleared the "
      "single bars (a parlay doesn't hold a single back).")
