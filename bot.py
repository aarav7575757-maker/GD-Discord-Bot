import discord
from discord import app_commands, File
from discord.ext import commands
import json
from datetime import datetime
import matplotlib.pyplot as plt
import os

# --------------------------
# CONFIG
# --------------------------
TOKEN = os.getenv("DISCORD_TOKEN")  # Set your bot token as an environment variable
DATA_FILE = "points.json"           # Total points
DAILY_FILE = "daily_points.json"    # Daily points
SUBMISSIONS_FILE = "submissions.json"

# --------------------------
# UTILITY FUNCTIONS
# --------------------------
def load_json(file_path):
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("{}")
    with open(file_path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# Points system
POINTS = {
    "Auto": 0,
    "Easy": 1,
    "Normal": 3,
    "Hard": 6,
    "Harder": 14,
    "Insane": 32,
    "Tier 1 Demon": 50,
    "Tier 2 Demon": 115,
    "Tier 3 Demon": 190,
    "Tier 4 Demon": 275,
    "Tier 5 Demon": 355,
    "Tier 6 Demon": 445,
    "Tier 7 Demon": 575,
    "Tier 8 Demon": 700,
    "Tier 9 Demon": 850,
    "Tier 10 Demon": 1025,
    "Tier 11 Demon": 1125,
    "Tier 12 Demon": 1300,
    "Tier 13 Demon": 1500,
    "Tier 14 Demon": 1725,
    "Tier 15 Demon": 1975,
    "Tier 16 Demon": 2275,
    "Tier 17 Demon": 2600,
    "Tier 18 Demon": 2950,
    "Tier 19 Demon": 2325,
    "Tier 20 Demon": 2725,
    "Extreme": 3125
}

# --------------------------
# CLIENT SETUP
# --------------------------
intents = discord.Intents.default()
client = commands.Bot(command_prefix="!", intents=intents)
tree = client.tree

# --------------------------
# BOT EVENTS
# --------------------------
@client.event
async def on_ready():
    await tree.sync()  # Sync commands
    print(f"Logged in as {client.user}")

# --------------------------
# /submit COMMAND
# --------------------------
@tree.command(name="submit", description="Submit a level completion")
@app_commands.describe(user="User who completed", difficulty="Level difficulty", amount="Number of completions (default 1)")
async def submit(interaction: discord.Interaction, user: discord.Member, difficulty: str, amount: int = 1):
    difficulty = difficulty.title()
    if difficulty not in POINTS:
        await interaction.response.send_message(f"Invalid difficulty: {difficulty}", ephemeral=True)
        return

    points = POINTS[difficulty] * amount

    # Update total points
    total_data = load_json(DATA_FILE)
    total_data[str(user.id)] = total_data.get(str(user.id), 0) + points
    save_json(DATA_FILE, total_data)

    # Update daily points
    daily_data = load_json(DAILY_FILE)
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in daily_data:
        daily_data[today] = {}
    daily_data[today][str(user.id)] = daily_data[today].get(str(user.id), 0) + points
    save_json(DAILY_FILE, daily_data)

    await interaction.response.send_message(f"{user.display_name} gained {points} points for {amount} x {difficulty} completions!")

# --------------------------
# /leaderboard COMMAND
# --------------------------
@tree.command(name="leaderboard", description="Show total points leaderboard")
async def leaderboard(interaction: discord.Interaction):
    total_data = load_json(DATA_FILE)
    if not total_data:
        await interaction.response.send_message("No submissions yet!")
        return
    sorted_data = sorted(total_data.items(), key=lambda x: x[1], reverse=True)
    msg = "**Leaderboard:**\n"
    for i, (uid, pts) in enumerate(sorted_data[:10], start=1):
        member = await interaction.guild.fetch_member(int(uid))
        msg += f"{i}. {member.display_name}: {pts} points\n"
    await interaction.response.send_message(msg)

# --------------------------
# /graph COMMAND
# --------------------------
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
        plt.savefig("/app/leaderboard.png")
        plt.close()

        await interaction.followup.send(file=File("/app/leaderboard.png"))

    except Exception as e:
        await interaction.followup.send(f"Error generating graph: {e}")

# --------------------------
# RUN THE BOT
# --------------------------
client.run(TOKEN)


