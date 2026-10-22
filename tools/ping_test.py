"""A test ping, exactly like a real alert's: posts to the +EV alerts channel and pings the DraftKings and FanDuel
roles (BOOK_ROLES), so whoever has those roles should get a notification. Run it on the server:

    sudo -u arbbot python3 /opt/arb-bot/tools/ping_test.py

It prints what Discord answered: "sent" means the message went out (if it shows in the channel but your phone
stayed quiet, the cause is a Discord or phone setting, not the bot)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import arbbot  # noqa: E402

arbbot.load_settings()
cfg = arbbot.Config.from_env()
url = cfg.ev_webhook_url or cfg.webhook_url
if not url:
    sys.exit("No alert webhook set (DISCORD_EV_WEBHOOK_URL / DISCORD_WEBHOOK_URL in /opt/arb-bot/.env).")
mention = " ".join(m for m in (arbbot.book_role_mention(cfg, b) for b in ("DraftKings", "FanDuel")) if m)
if not mention:
    print("No DraftKings/FanDuel roles in BOOK_ROLES: the test goes out without a ping.")
payload = {"username": arbbot.BOT_NAME, "content": f"{mention} 🔔 Test notification: if your phone buzzed, alerts "
           "will reach you. Nothing to bet.".strip(), "allowed_mentions": arbbot.allowed_mentions(mention)}
try:
    arbbot._webhook(url, payload)
except Exception as e:  # noqa: BLE001
    sys.exit(f"Discord refused it: {e!r:.300}")
print(f"sent (pinged: {mention or 'nobody'})")
