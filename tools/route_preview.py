"""Where each of a day's alerts WOULD go with ROUTING on, and who it would ping. Posts nothing. On the server:

    sudo -u arbbot python3 /opt/arb-bot/tools/route_preview.py [YYYY-MM-DD]

The day (New York, by game start) defaults to today. Reads the bet logs (+EV, props, outliers, parlays) and the
server's roles (by name, with the bot token), then prints each alert with its channels: the main feed, its
sport's channel (the only copy that pings, with the roles it pings), the elite channel when it's 💎 Elite, and its
play type's channel. A role the server doesn't have is named once at the top."""
import sys
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import arbbot  # noqa: E402

arbbot.load_settings()
cfg = arbbot.Config.from_env()
cfg = arbbot.replace(cfg, routing=True)
day = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.now(ZoneInfo(cfg.timezone)).date()
if not cfg.channels.get("main"):
    sys.exit("No CHANNELS main=... set: nothing to route.")
roles = arbbot.route_roles(cfg)
names = {v: k for k, v in cfg.channels.items()} | {v: k.lower() for k, v in cfg.sport_channels.items()}


def item(r: dict):
    fair = 1 / float(r["fair_odds"]) if r.get("fair_odds") not in ("", None) else 0.0
    return SimpleNamespace(sport_key=r.get("sport_key", ""), book=r.get("book", ""), fair_prob=fair,
                           confidence=r.get("confidence", ""), player=r.get("player", ""),
                           sharp_prob=float(r["pinnacle_prob"]) if r.get("pinnacle_prob") not in ("", None) else None)


n = 0
for kind, name in (("ev", cfg.ev_log_file), ("line", cfg.outlier_log_file)):
    for r in arbbot._read_csv(name) if name else []:
        if arbbot.local_day(cfg, r["commence_time"]) != day:
            continue
        it = item(r)
        typ = kind if kind == "line" else ("prop" if it.player else "")
        targets, pings = arbbot.route(cfg, it, typ, roles)
        what = f"{r.get('player', '')} {r['outcome']} {r.get('point', '')}".strip()
        print(f"{r['first_seen'][11:16]} {r.get('sport', '')} · {what[:44]} {r['price']} @ {r['book']}")
        print(arbbot.route_preview(targets, pings, roles))
        n += 1
for r in arbbot._read_csv(cfg.parlay_log_file) if cfg.parlay_log_file else []:
    row = arbbot._parlay_row(r)
    if row and arbbot.local_day(cfg, row["commence_time"]) == day:
        targets, pings = arbbot.route(cfg, SimpleNamespace(sport_key="parlay", book=r["book"], fair_prob=0.0), "", roles)
        print(f"{r['first_seen'][11:16]} Parlay · {r['legs'][:60]} @ {r['book']}")
        print(arbbot.route_preview(targets, pings, roles))
        n += 1
print(f"\n{n} alerts on {day}. Nothing was posted.")
