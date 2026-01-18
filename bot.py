import discord
from discord import app_commands, File
from discord.ext import commands
import json
from datetime import datetime
import matplotlib.pyplot as plt
import os

# ---------- CONFIG ----------
TOKEN = os.getenv("DISCORD_TOKEN")  # set your token in Railway environment variables
GUILD_ID = None  # set your guild ID if you want commands to be guild-specific for faster registration

# JSON files
POINTS_FILE = "points.json"
SUBMISSIONS_FILE = "submissions.json"
DAILY_FILE = "daily_points.json"

# Points per difficulty
POINTS = {
    "Auto": 0, "Easy": 1, "Normal": 3, "Hard": 6, "Harder": 14,
    "Insane": 32, "Tier 1 Demon": 50, "Tier 2 Demon": 115, "Tier 3 Demon": 190,
    "Tier 4 Demon": 275, "Tier 5 Demon": 355, "Tier 6 Demon": 445, "Tier 7 Demon": 575,
    "Tier 8 Demon": 700, "Tier 9 Demon": 850, "Tier 10 Demon": 1025, "Tier 11 Demon": 1125,
    "Tier 12 Demon": 1300, "Tier 13 Demon": 1500, "Tier 14 Demon": 1725, "Tier 15 Demon": 1975,
    "Tier 16 Demon": 2275, "Tier 17 Demon": 2600, "Tier 18 Demon": 2950, "Tier 19 Demon": 2325,
    "Tier 20 Demon": 2725, "Extreme": 3125
}

# ---------- BOT SETUP ----------
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)
tree = client.tree

# ---------- HELPER FUNCTIONS ----------
@tree.command(name="graph", description="Show daily total points graph")
async def graph(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        data = load_json(DAILY_FILE)

        today = datetime.now().strftime("%Y-%m-%d")
        if today not in data:
            data[today] = {}

        all_users = set()
        for day in data:
            all_users.update(data[day].keys())
        all_users = sorted(all_users)
        if not all_users:
            await interaction.followup.send("No submissions yet.")
            return

        days = sorted(data.keys())
        lines = {user: [] for user in all_users}
        for day in days:
            for user in all_users:
                lines[user].append(data[day].get(user, 0))

        plt.figure(figsize=(10,6))
        for user, points in lines.items():
            plt.plot(days, points, marker='o', label=user)

        plt.xticks(rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Points")
        plt.title("Daily Leaderboard")
        plt.legend()
        plt.tight_layout()
        plt.savefig("/app/leaderboard.png")  # Railway-safe path
        plt.close()

        await interaction.followup.send(file=File("/app/leaderboard.png"))

    except Exception as e:
        await interaction.followup.send(f"Error generating graph: {e}")


    user = str(interaction.user)
    total_points = add_points(user, difficulty, amount)
    add_daily_points(user, POINTS[difficulty] * amount)
    add_submission(user, difficulty, amount)

    await interaction.response.send_message(f"{interaction.user.mention} submitted {amount}x {difficulty} ✅ Total points: {total_points}")

# ---------- /graph COMMAND ----------
@tree.command(name="graph", description="Show daily total points graph")
async def graph(interaction: discord.Interaction):
    await interaction.response.defer()
    data = load_json(DAILY_FILE)

    today = datetime.now().strftime("%Y-%m-%d")
    if today not in data:
        data[today] = {}

    if not data:
        await interaction.followup.send("No submissions yet.")
        return

    all_users = set()
    for day in data:
        all_users.update(data[day].keys())
    all_users = sorted(all_users)
    if not all_users:
        await interaction.followup.send("No submissions yet.")
        return

    days = sorted(data.keys())
    lines = {user: [] for user in all_users}
    for day in days:
        for user in all_users:
            lines[user].append(data[day].get(user, 0))

    plt.figure(figsize=(10,6))
    for user, points in lines.items():
        plt.plot(days, points, marker='o', label=user)

    plt.xticks(rotation=45)
    plt.xlabel("Date")
    plt.ylabel("Points")
    plt.title("Daily Leaderboard")
    plt.legend()
    plt.tight_layout()
    plt.savefig("leaderboard.png")
    plt.close()

    await interaction.followup.send(file=File("leaderboard.png"))

# ---------- ON READY ----------
@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")

# ---------- RUN BOT ----------
client.run(TOKEN)


