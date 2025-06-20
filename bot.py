import asyncio
import random
import logging
import os
from collections import deque
from aiohttp import web
from telethon import TelegramClient, events

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load credentials from environment
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session_name = os.getenv("SESSION_NAME", "your_session")

client = TelegramClient(f"{session_name}.session", api_id, api_hash)

# Cooldown state
state = {
    "cooldown": random.randint(1, 2)
}

# Pokémon sets
legendary_poks_safari = [
    "Rayquaza", "Kyogre", "Groudon", "Dialga", "Kyurem", "Reshiram", "Zekrom", "Yveltal",
    "Xerneas", "Zygarde", "Cosmog", "Cosmoem", "Necrozma", "Ho-oh", "Lugia", "Arceus",
    "Zeraora", "Pheromosa", "Mewtwo", "Victini", "Regigigas", "Deoxys", "Marshadow"
]
regular_poks_safari = [
    "Charizard", "Blastoise", "Mankey", "Primeape", "Abra", "Alakazam", "Magikarp", "Gyarados",
    "Porygon", "Aerodactyl", "Staryu", "Snorlax"
]

repeat_ball = regular_poks_safari + legendary_poks_safari
last_two_messages = deque(maxlen=2)

# Event handlers
@client.on(events.NewMessage(from_users=572621020))
async def handle_limits(event):
    if "Daily hunt limit reached" in event.raw_text or \
       "You have run out of Safari Balls and are now exiting the Hoenn Safari Zone" in event.raw_text:
        logging.info("Limit reached or balls finished. Disconnecting.")
        await client.disconnect()

@client.on(events.NewMessage(from_users=572621020))
async def handle_shiny(event):
    if "✨ Shiny pokemon found!" in event.raw_text:
        logging.info("Shiny detected! Alerting and exiting.")
        await client.send_message(-1005973904185, "@username  shiny aaya jaldi dekho")
        await client.disconnect()

@client.on(events.NewMessage(from_users=572621020))
async def handle_hunt(event):
    if "A wild" in event.raw_text:
        pok_name = event.raw_text.split("wild ")[1].split(" (")[0]
        logging.info(f"Wild Pokémon detected: {pok_name}")
        await asyncio.sleep(state["cooldown"])
        if pok_name in repeat_ball:
            await event.click(0, 0)
        else:
            await client.send_message(572621020, '/hunt')

@client.on(events.NewMessage(from_users=572621020))
async def handle_battle_start(event):
    if "Safari Balls:" in event.raw_text:
        await asyncio.sleep(state["cooldown"])
        await event.click(0, 0)

@client.on(events.MessageEdited(from_users=572621020))
async def handle_battle_edit(event):
    if "Safari Balls:" in event.raw_text:
        await asyncio.sleep(state["cooldown"])
        await event.click(0, 0)

async def handle_skip_or_hunt(event):
    text = event.raw_text.lower()
    if any(x in text for x in ["fled", "your safari ball failed", "you caught", "💵"]):
        await asyncio.sleep(state["cooldown"])
        await client.send_message(572621020, '/hunt')

@client.on(events.NewMessage(from_users=572621020))
async def handle_result(event):
    await handle_skip_or_hunt(event)

@client.on(events.MessageEdited(from_users=572621020))
async def handle_result_edit(event):
    await handle_skip_or_hunt(event)

@client.on(events.NewMessage(from_users=572621020))
async def handle_trainer(event):
    if "An expert trainer" in event.raw_text:
        logging.info("Trainer detected. Skipping.")
        await asyncio.sleep(state["cooldown"])
        await client.send_message(572621020, '/hunt')

# HTTP server for Render health checks
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()
    logging.info("HTTP server started on port 10000.")

# Entry point
async def main():
    await client.start()
    await start_web_server()
    logging.info("Telethon bot started.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
