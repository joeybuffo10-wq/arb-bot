"""A test phone notification through ntfy (NTFY_TOPIC), the backup to Discord. Run it on the server:

    sudo -u arbbot python3 /opt/arb-bot/tools/ntfy_test.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import arbbot  # noqa: E402

arbbot.load_settings()
cfg = arbbot.Config.from_env()
if not cfg.ntfy_topic:
    sys.exit("NTFY_TOPIC isn't set yet: sudo -u arbbot python3 /opt/arb-bot/arbbot.py --set NTFY_TOPIC=your-topic")
ok = arbbot.ntfy_push(cfg, {"embeds": [{"title": "🔔 Buff Bets test", "description":
                                        "If this reached your phone, new alerts will too."}]})
print("sent: check your phone" if ok else "ntfy didn't take it (see the error above)")
