import discord
from discord import app_commands
import json
import os
from datetime import date
import matplotlib.pyplot as plt

# ================= CONFIG =================

TOKEN = os.getenv("DISCORD_TOKEN")

DATA_FILE = "points.json"
DAILY_FILE = "daily_points.json"

DIFFICULTY_POINTS = {
    "easy": 1,
    "normal": 2,
    "hard": 3,
    "insane": 4,
    "extreme": 5
}

# ================= HELPERS =================

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ================= BOT =================

intents = discord.Intents.default()

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ================= EVENTS =================

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")

# ================= COMMANDS =================

@tree.command(name="submit", description="Submit level completions (multiple difficulties allowed)")
@app_commands.describe(
    easy="Number of easy levels",
    normal="Number of normal levels",
    hard="Number of hard levels",
    insane="Number of insane levels",
    extreme="Number of extreme levels"
)
async def submit(
    interaction: discord.Interaction,
    easy: int = 0,
    normal: int = 0,
    hard: int = 0,
    insane: int = 0,
    extreme: int = 0
):
    await interaction.response.defer()

    total_points = (
        easy * DIFFICULTY_POINTS["easy"] +
        normal * DIFFICULTY_POINTS["normal"] +
        hard * DIFFICULTY_POINTS["hard"] +
        insane * DIFFICULTY_POINTS["insane"] +
        extreme * DIFFICULTY_POINTS["extreme"]
    )

    if total_points <= 0:
        await interaction.followup.send("You must submit at least one level.")
        return

    uid = str(interaction.user.id)
    today = str(date.today())

    total_data = load_json(DATA_FILE)
    daily_data = load_json(DAILY_FILE)

    total_data[uid] = total_data.get(uid, 0) + total_points

    if today not in daily_data:
        daily_data[today] = {}
    daily_data[today][uid] = daily_data[today].get(uid, 0) + total_points

    save_json(DATA_FILE, total_data)
    save_json(DAILY_FILE, daily_data)

    await interaction.followup.send(
        f"✅ Submitted **{total_points} points**!\n"
        f"Easy: {easy}, Normal: {normal}, Hard: {hard}, Insane: {insane}, Extreme: {extreme}"
    )

# ================= LEADERBOARD =================

@tree.command(name="leaderboard", description="Show total points leaderboard")
async def leaderboard(interaction: discord.Interaction):
    await interaction.response.defer()

    total_data = load_json(DATA_FILE)
    if not total_data:
        await interaction.followup.send("No data yet.")
        return

    sorted_data = sorted(total_data.items(), key=lambda x: x[1], reverse=True)

    msg = "**🏆 Leaderboard**\n"
    for i, (uid, pts) in enumerate(sorted_data[:10], start=1):
        member = interaction.guild.get_member(int(uid))
        name = member.display_name if member else f"User {uid}"
        msg += f"{i}. {name}: **{pts}** points\n"

    await interaction.followup.send(msg)

# ================= GRAPH =================

@tree.command(name="graph", description="Show daily total points graph")
async def graph(interaction: discord.Interaction):
    await interaction.response.defer()

    daily_data = load_json(DAILY_FILE)
    if not daily_data:
        await interaction.followup.send("No data yet.")
        return

    dates = sorted(daily_data.keys())
    totals = []

    for d in dates:
        totals.append(sum(daily_data[d].values()))

    # Always show first day
    plt.figure()
    plt.plot(dates, totals, marker="o")
    plt.title("Daily Total Points")
    plt.xlabel("Date")
    plt.ylabel("Points")
    plt.xticks(rotation=45)
    plt.tight_layout()

    path = "graph.png"
    plt.savefig(path)
    plt.close()

    await interaction.followup.send(file=discord.File(path))

@tree.command(name="ping", description="Test command")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")


# ================= RUN =================

client.run(TOKEN)


