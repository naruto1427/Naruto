import os
import asyncio
import random
import re
import logging
from collections import deque
from aiohttp import web
from telethon import TelegramClient, events

logging.basicConfig(level=logging.INFO)

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session_name = os.getenv("SESSION_NAME", "poke_session")

client = TelegramClient(f"{session_name}.session", api_id, api_hash)

cooldown = random.randint(1, 2)
low_lvl = False
last_two_messages = deque(maxlen=2)

legendary_poks = ["Rayquaza", "Kyogre", "Groudon", "Dialga", "Kyurem", "Reshiram", "Zekrom", "Yveltal",
                  "Xerneas", "Zygarde", "Cosmog", "Cosmoem", "Necrozma", "Ho-oh", "Lugia", "Arceus",
                  "Zeraora", "Pheromosa", "Mewtwo", "Victini", "Regigigas", "Deoxys", "Marshadow"]

regular_poks_repeat = ["Floette", "flabebe", "Munchlax", "Conkeldurr", "Timburr", "Gurdurr", "Chandelure",
                       "Litwick", "Lampent", "Goomy", "Sliggoo", "Goodra", "Greninja", "Frogadier", "Froakie",
                       "Haxorus", "Fraxure", "Axew", "Ferroseed", "Ferrothorn", "Staraptor", "Heracross", "Aerodactyl"]

regular_ball = regular_poks_repeat.copy()
repeat_ball = regular_poks_repeat + legendary_poks

# === Utility ===
def calculate_health_percentage(max_hp, current_hp):
    if max_hp <= 0: return 0
    return round((current_hp / max_hp) * 100)

# === Bot Logic ===
@client.on(events.NewMessage(from_users=572621020))
async def handle_limit(event):
    if "Daily hunt limit reached" in event.raw_text:
        await client.disconnect()

@client.on(events.NewMessage(from_users=572621020))
async def handle_shiny_or_hunt(event):
    global cooldown
    if "✨ Shiny pokemon found!" in event.raw_text:
        await event.client.send_message(-1005973904185, "@username shiny aaya jaldi dekho")
        await client.disconnect()
    elif "A wild" in event.raw_text:
        pok_name = event.raw_text.split("wild ")[1].split(" (")[0]
        print("Wild:", pok_name)
        await asyncio.sleep(cooldown)
        if pok_name in repeat_ball or pok_name in regular_ball:
            await event.click(0, 0)
        else:
            await client.send_message(572621020, '/hunt')

@client.on(events.NewMessage(from_users=572621020))
async def handle_battle_start(event):
    global low_lvl, cooldown
    if "Battle begins!" in event.raw_text:
        hp_match = re.search(r"HP (\d+)/(\d+)", event.raw_text)
        if hp_match:
            max_hp = int(hp_match.group(2))
            if max_hp <= 50:
                low_lvl = True
                await asyncio.sleep(cooldown)
                await event.click(text="Poke Balls")
            else:
                await asyncio.sleep(2)
                await event.click(0, 0)

@client.on(events.MessageEdited(from_users=572621020))
async def handle_battle_edit(event):
    global low_lvl, cooldown
    if "Wild" in event.raw_text:
        hp_match = re.search(r"HP (\d+)/(\d+)", event.raw_text)
        name_match = re.search(r"Wild (\w+)", event.raw_text)
        if hp_match and name_match:
            current, max_hp = map(int, hp_match.groups())
            percent = calculate_health_percentage(max_hp, current)
            pok_name = name_match.group(1)

            if low_lvl or percent <= 50:
                await asyncio.sleep(cooldown)
                await event.click(text="Poke Balls")
                if pok_name in regular_ball or pok_name in repeat_ball:
                    await asyncio.sleep(1)
                    await event.click(text="Repeat")
            else:
                await asyncio.sleep(1)
                await event.click(0, 0)

@client.on(events.MessageEdited(from_users=572621020))
async def skip_on_flee_or_catch(event):
    global low_lvl, cooldown
    if any(x in event.raw_text for x in ["fled", "💵", "You caught"]):
        low_lvl = False
        await asyncio.sleep(cooldown)
        await client.send_message(572621020, '/hunt')

@client.on(events.NewMessage(from_users=572621020))
async def skip_trainer(event):
    if "An expert trainer" in event.raw_text:
        await asyncio.sleep(cooldown)
        await client.send_message(572621020, '/hunt')

@client.on(events.MessageEdited(from_users=572621020))
async def switch_pokemon(event):
    if "Choose your next pokemon." in event.raw_text:
        for name in ["Zorua", "Terrakion", "Golett", "scizor", "zoroark"]:
            try:
                await event.click(text=name)
                break
            except:
                continue

# === Minimal HTTP server ===
async def handle(request):
    return web.Response(text="Bot is running.")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()
    logging.info("Web server running on port 10000.")

# === Main ===
async def main():
    await client.start()
    await start_web_server()
    logging.info("Bot started.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
