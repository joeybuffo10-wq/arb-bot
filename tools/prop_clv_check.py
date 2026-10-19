"""Why do a sport's player props lose to the closing line? Reads the bot's own logs (run it on the server):

    sudo -u arbbot python3 /opt/arb-bot/tools/prop_clv_check.py [SPORT_KEY] [SINCE]

SPORT_KEY defaults to americanfootball_nfl, SINCE (YYYY-MM-DD, by kickoff) to 2026-10-11. Prints the props'
beat-the-close rate by side (Over/Under) and by where the fair price came from, by how long before kickoff
the alert went out, and then every Under: its fair chance when alerted, Pinnacle's and Kalshi's, and the
closing chance, so a fair price that was off from the start stands out from a line that moved later."""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import arbbot  # noqa: E402

sport = sys.argv[1] if len(sys.argv) > 1 else "americanfootball_nfl"
since = datetime.fromisoformat(sys.argv[2] if len(sys.argv) > 2 else "2026-10-11").replace(tzinfo=timezone.utc)

arbbot.load_settings()
cfg = arbbot.Config.from_env()
rows = [r for r in arbbot.clv_rows(cfg) if r.get("sport_key") == sport and r.get("player")
        and arbbot._parse_time(r["commence_time"]) >= since]
if not rows:
    sys.exit(f"No {sport} player props with a closing line since {since:%Y-%m-%d}.")


def hours(r):
    return (arbbot._parse_time(r["commence_time"]) - arbbot._parse_time(r["first_seen"])).total_seconds() / 3600


def pct(x):
    return f"{float(x) * 100:5.1f}" if x not in ("", None) else "    -"


def table(title, key):
    groups = {}
    for r in rows:
        groups.setdefault(key(r), []).append(r)
    print(f"\n{title}")
    for name, rs in sorted(groups.items(), key=lambda t: -len(t[1])):
        beat = sum(r["beat_close"] for r in rs)
        avg = sum(r["clv_pct"] for r in rs) / len(rs)
        print(f"  {name:<34} {len(rs):>4} bets  beat the close {beat:>3}/{len(rs):<3} ({beat / len(rs) * 100:3.0f}%)"
              f"  avg CLV {avg:+5.1f}%")


side = lambda r: r["outcome"]
table("By side", side)
table("By side and fair price source", lambda r: f"{side(r)} · {arbbot._fair_group(r)}")
table("By side and hours before kickoff", lambda r: f"{side(r)} · " + next(
    name for cut, name in ((1, "under 1h"), (3, "1-3h"), (8, "3-8h"), (24, "8-24h"), (1e9, "over 24h"))
    if hours(r) < cut))
table("By side and book", lambda r: f"{side(r)} · {r.get('book', '?')}")

print("\nEvery Under (win chances in %: fair when alerted, Pinnacle, Kalshi, at the close)")
print(f"  {'bet':<44} {'book':<11} {'price':>6} {'fair':>5} {'pinn':>5} {'kals':>5} {'close':>5} {'hrs':>5}  from")
for r in sorted((r for r in rows if r["outcome"] == "Under"), key=lambda r: r["first_seen"]):
    bet = f"{r['player']} {float(r['point']):g} {arbbot.MARKET_NAMES.get(r['market'], r['market'])}"
    print(f"  {bet[:44]:<44} {r.get('book', '')[:11]:<11} {float(r['price']):6.2f} {pct(1 / float(r['fair_odds']))}"
          f" {pct(r.get('pinnacle_prob'))} {pct(r.get('kalshi_prob'))} {pct(1 / r['closing_fair_odds'])}"
          f" {hours(r):5.1f}  {r.get('fair_from', '')[:40]}")
