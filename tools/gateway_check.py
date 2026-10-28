"""Can the bot hold a live connection to Discord (INTERACTIONS)? Connects, logs in, prints what Discord says,
and disconnects. Registers nothing and posts nothing. On the server:

    sudo -u arbbot python3 /opt/arb-bot/tools/gateway_check.py"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import arbbot  # noqa: E402

arbbot.load_settings()
cfg = arbbot.Config.from_env()
if not cfg.discord_bot_token:
    sys.exit("No DISCORD_BOT_TOKEN.")
url = (arbbot._bot_api(cfg.discord_bot_token, "GET", "/gateway/bot") or {}).get("url", "wss://gateway.discord.gg")
sock = arbbot.ws_connect(f"{url}/?v=10&encoding=json")
hello = json.loads(arbbot.ws_recv(sock))
print(f"Connected to {url}: heartbeat every {hello['d']['heartbeat_interval'] / 1000:.0f}s")
sock.sendall(arbbot.ws_frame(1, json.dumps({"op": 2, "d": {"token": cfg.discord_bot_token, "intents": 1,
                                                          "properties": {"os": "linux", "browser": "arbbot",
                                                                         "device": "arbbot"}}}).encode()))
sock.settimeout(15)
end = time.time() + 15
while time.time() < end:
    msg = json.loads(arbbot.ws_recv(sock) or "{}")
    if msg.get("t") == "READY":
        d = msg["d"]
        guilds = [g["id"] for g in d.get("guilds", [])]
        print(f"✅ Logged in as {d['user']['username']} (app {d['application']['id']}); in {len(guilds)} server(s)"
              + (" including Buff Bets" if cfg.guild_id in guilds else f" — NOT in GUILD_ID {cfg.guild_id}"))
        break
    if msg.get("op") == 9:
        sys.exit("❌ Discord turned the login down (op 9): check the token.")
else:
    print("❌ No READY from Discord within 15s.")
sock.sendall(arbbot.ws_frame(8, b""))
