"""How ESPN reports when UFC fights ended, as the total-rounds grading reads it (run it on the server):

    sudo -u arbbot python3 /opt/arb-bot/tools/ufc_check.py [YYYYMMDD]

The date of a card (default 20261017). Each fight: the fighters, ESPN's round, clock (m:ss and seconds) and
whether it's over, then the length the grading works out in rounds (2.5 = halfway into round 3; a decision
= 3.0, or 5.0 for a main event; None = ESPN doesn't say, so such bets go to you by hand)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import arbbot  # noqa: E402

day = sys.argv[1] if len(sys.argv) > 1 else "20261017"
data = arbbot._espn(f"mma/ufc/scoreboard?dates={day}")
fights = [c for e in data.get("events", []) for c in e.get("competitions", [])]
if not fights:
    sys.exit(f"ESPN lists no UFC fights on {day}.")
for c in fights:
    st = c.get("status", {})
    names = " vs ".join(x.get("athlete", {}).get("displayName", "?") for x in c.get("competitors", []))
    print(f"{names[:46]:<46} round {st.get('period')}  clock {st.get('displayClock')} ({st.get('clock')}s)  "
          f"over: {st.get('type', {}).get('completed')}  ->  {arbbot.fight_length(c)}")
