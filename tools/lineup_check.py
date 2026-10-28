"""What the lineup channels would get from ESPN's injury reports right now. Posts nothing. On the server:

    sudo -u arbbot python3 /opt/arb-bot/tools/lineup_check.py

For each sport ESPN has (NFL, NCAAF, NBA, NCAAB, MLB, NHL): how many statuses its report has, and the newest 5 as
the bot would write them. (The bot itself only posts what changes after its first read.)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import arbbot  # noqa: E402

for sport, key in arbbot.LINEUP_SPORTS.items():
    try:
        data = arbbot._get_json(f"{arbbot.ESPN_BASE}/{arbbot.ESPN_LEAGUES[key][0]}/injuries")
    except Exception as e:  # noqa: BLE001
        print(f"{sport}: couldn't read ESPN ({e!r:.100})")
        continue
    ups = sorted(arbbot.espn_injuries(data), key=lambda u: u.get("date", ""), reverse=True)
    print(f"\n{sport}: {len(ups)} statuses")
    for u in ups[:5]:
        print("  " + arbbot.lineup_line(sport, u))
