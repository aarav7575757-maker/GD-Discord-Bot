import discord
from discord import app_commands
import json
import os
import matplotlib.pyplot as plt
from datetime import date

# ================== CONFIG ==================
TOKEN = "enter token here"
COMPLETION_CHANNEL_ID = 1423980603878932692  # replace with your channel ID

DATA_FILE = "points.json"
SUBMISSIONS_FILE = "submissions.json"
HISTORY_FILE = "history.json"
GRAPH_FILE = "leaderboard.png"

# ================== POINTS TABLE ==================
POINTS = {
    "auto": 0,
    "easy": 1,
    "normal": 3,
    "hard": 6,
    "harder": 14,
    "insane": 32,
    "tier 1 demon": 50,
    "tier 2 demon": 115,
    "tier 3 demon": 190,
    "tier 4 demon": 275,
    "tier 5 demon": 355,
    "tier 6 demon": 445,
    "tier 7 demon": 575,
    "tier 8 demon": 700,
    "tier 9 demon": 850,
    "tier 10 demon": 1025,
    "tier 11 demon": 1125,
    "tier 12 demon": 1300,
    "tier 13 demon": 1500,
    "tier 14 demon": 1725,
    "tier 15 demon": 1975,
    "tier 16 demon": 2275,
    "tier 17 demon": 2600,
    "tier 18 demon": 2950,
    "tier 19 demon": 2325,
    "tier 20 demon": 2725,
    "extreme": 3125
}

# ================== BOT SETUP ==================
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ================== FILE HELPERS ==================
def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

points_data = load_json(DATA_FILE)
submissions = load_json(SUBMISSIONS_FILE)
history = load_json(HISTORY_FILE)

# ================== HISTORY UPDATE ==================
def update_daily_history():
    today = date.today().isoformat()
    total_points = sum(points_data.values())
    history[today] = total_points
    save_json(HISTORY_FILE, history)

# ================== READY ==================
@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot online as {client.user}")
    print("✅ Slash commands synced")

# ================== SLASH COMMANDS ==================

@tree.command(name="leaderboard", description="Show the top players")
async def leaderboard(interaction: discord.Interaction):
    if not points_data:
        await interaction.response.send_message("No points yet.")
        return

    sorted_players = sorted(points_data.items(), key=lambda x: x[1], reverse=True)

    embed = discord.Embed(title="🏆 Leaderboard", color=0xffd700)
    for i, (player, pts) in enumerate(sorted_players[:10], start=1):
        embed.add_field(name=f"{i}. {player}", value=f"{pts} points", inline=False)

    await interaction.response.send_message(embed=embed)

@tree.command(name="stats", description="Check a player's points")
@app_commands.describe(player="Player name")
async def stats(interaction: discord.Interaction, player: str):
    pts = points_data.get(player, 0)
    await interaction.response.send_message(
        f"**{player}** has **{pts}** points."
    )

@tree.command(name="graph", description="Show daily total points graph")
async def graph(interaction: discord.Interaction):
    if len(history) < 2:
        await interaction.response.send_message(
            "Not enough data yet. Graph updates daily.",
            ephemeral=True
        )
        return

    dates = list(history.keys())
    totals = list(history.values())

    plt.figure()
    plt.plot(dates, totals, marker="o")
    plt.xticks(rotation=45)
    plt.xlabel("Date")
    plt.ylabel("Total Points")
    plt.title("Daily Total Points Progress")
    plt.tight_layout()
    plt.savefig(GRAPH_FILE)
    plt.close()

    await interaction.response.send_message(
        file=discord.File(GRAPH_FILE)
    )

# ================== COMPLETION HANDLER ==================
@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id != COMPLETION_CHANNEL_ID:
        return

    try:
        lines = message.content.lower().splitlines()
        info = {}
        total_points = 0
        breakdown = []

        for line in lines:
            if ":" in line:
                k, v = line.split(":", 1)
                info[k.strip()] = v.strip()

        if "player" not in info:
            await message.reply("❌ Missing Player.")
            return

        player = info["player"]
        level = info.get("level", "Multiple / None")

        points_data.setdefault(player, 0)
        submissions.setdefault(player, [])

        for key, value in info.items():
            if key in POINTS:
                try:
                    amount = int(value)
                except ValueError:
                    amount = 1

                earned = POINTS[key] * amount
                total_points += earned
                breakdown.append(f"{key.title()} × {amount} = {earned}")

        if total_points == 0:
            await message.reply("❌ No valid difficulties found.")
            return

        points_data[player] += total_points
        save_json(DATA_FILE, points_data)
        update_daily_history()

        embed = discord.Embed(title="✅ Completion Recorded", color=0x00ff00)
        embed.add_field(name="Player", value=player, inline=False)
        embed.add_field(name="Level", value=level, inline=False)
        embed.add_field(name="Breakdown", value="\n".join(breakdown), inline=False)
        embed.add_field(name="Points Earned", value=total_points, inline=True)
        embed.add_field(name="Total Points", value=points_data[player], inline=True)

        await message.reply(embed=embed)

    except Exception as e:
        print("ERROR:", e)

# ================== RUN ==================
client.run(TOKEN)
