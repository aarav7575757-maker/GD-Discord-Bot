import discord
from discord import app_commands
import json
import os
from datetime import date
import matplotlib.pyplot as plt

TOKEN = os.getenv("DISCORD_TOKEN")  # Railway / GitHub
# OR replace with string if local:
# TOKEN = "YOUR_BOT_TOKEN_HERE"

DATA_POINTS = "points.json"
DATA_SUBS = "submissions.json"
DATA_HISTORY = "history.json"

# ---------------- SAFE JSON ----------------

def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default, f)
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        with open(path, "w") as f:
            json.dump(default, f)
        return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

points = load_json(DATA_POINTS, {})
submissions = load_json(DATA_SUBS, [])
history = load_json(DATA_HISTORY, {})

# ---------------- DISCORD SETUP ----------------

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {client.user}")

# ---------------- POINT VALUES ----------------

POINTS = {
    "easy": 1,
    "normal": 2,
    "hard": 3,
    "harder": 4,
    "insane": 5,
    "demon": 10
}

# ---------------- /submit ----------------

@tree.command(name="submit", description="Submit beaten levels")
@app_commands.describe(
    difficulty="easy, normal, hard, harder, insane, demon",
    amount="How many levels",
    level_name="Optional level name"
)
async def submit(
    interaction: discord.Interaction,
    difficulty: str,
    amount: int,
    level_name: str | None = None
):
    await interaction.response.defer(ephemeral=True)

    difficulty = difficulty.lower()
    if difficulty not in POINTS or amount <= 0:
        await interaction.followup.send("❌ Invalid difficulty or amount")
        return

    uid = str(interaction.user.id)
    gained = POINTS[difficulty] * amount

    points[uid] = points.get(uid, 0) + gained
    save_json(DATA_POINTS, points)

    today = str(date.today())
    history.setdefault(today, {})
    history[today][uid] = points[uid]
    save_json(DATA_HISTORY, history)

    submissions.append({
        "user": uid,
        "difficulty": difficulty,
        "amount": amount,
        "level": level_name,
        "date": today
    })
    save_json(DATA_SUBS, submissions)

    await interaction.followup.send(
        f"✅ **{interaction.user.name}** gained **{gained} points**"
    )

# ---------------- /leaderboard ----------------

@tree.command(name="leaderboard", description="Show points leaderboard")
async def leaderboard(interaction: discord.Interaction):
    await interaction.response.defer()

    if not points:
        await interaction.followup.send("No data yet")
        return

    sorted_users = sorted(points.items(), key=lambda x: x[1], reverse=True)

    text = ""
    for i, (uid, pts) in enumerate(sorted_users[:10], start=1):
        user = await client.fetch_user(int(uid))
        text += f"**{i}. {user.name}** — {pts} pts\n"

    await interaction.followup.send(text)

# ---------------- /graph ----------------

@tree.command(name="graph", description="Daily total points graph")
async def graph(interaction: discord.Interaction):
    await interaction.response.defer()

    if not history:
        await interaction.followup.send("Not enough data yet")
        return

    dates = sorted(history.keys())
    users = set(uid for day in history.values() for uid in day)

    plt.figure()

    for uid in users:
        values = []
        last = 0
        for d in dates:
            if uid in history[d]:
                last = history[d][uid]
            values.append(last)

        user = await client.fetch_user(int(uid))
        plt.plot(dates, values, label=user.name)

    plt.xlabel("Date")
    plt.ylabel("Points")
    plt.title("Daily Points Progress")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig("graph.png")
    plt.close()

    await interaction.followup.send(file=discord.File("graph.png"))

# ---------------- RUN ----------------

client.run(TOKEN)
