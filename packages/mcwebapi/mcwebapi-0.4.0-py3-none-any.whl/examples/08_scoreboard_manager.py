"""
Scoreboard Manager
Creates and manages a scoreboard with player scores.
"""

import asyncio
from mcwebapi import MinecraftAPI


async def main():
    """Create and manage a scoreboard."""
    async with MinecraftAPI() as api:
        print("=== 🏆 Scoreboard Manager ===\n")

        scoreboard = api.Scoreboard()
        player = api.Player("Dev")

        # Create objective
        print("📊 Creating scoreboard objective...")
        objective_name = "python_score"
        await scoreboard.createObjective(
            objective_name,
            "dummy",
            "Python Score"
        )
        print(f"✅ Created objective: {objective_name}")

        # Set display slot
        print("\n📺 Setting sidebar display...")
        await scoreboard.setDisplaySlot("sidebar", objective_name)
        print("✅ Objective displayed on sidebar")

        # Add scores for demo
        print("\n📈 Adding scores...")
        players_scores = [
            ("Dev", 100),
            ("Steve", 85),
            ("Alex", 92),
            ("Notch", 150),
        ]

        for player_name, score in players_scores:
            await scoreboard.setScore(objective_name, player_name, score)
            print(f"  {player_name}: {score} points")

        # Get and display all scores
        print("\n🏅 Leaderboard:")
        scores = await scoreboard.getObjectiveScores(objective_name)

        # Sort by score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        for rank, (name, score) in enumerate(sorted_scores, 1):
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
            print(f"  {medal} {rank}. {name}: {score} points")

        # Increment score for current player
        print(f"\n➕ Adding 25 points to Dev...")
        await scoreboard.addScore(objective_name, "Dev", 25)

        # Get updated score
        dev_score = await scoreboard.getScore(objective_name, "Dev")
        print(f"✅ Dev's new score: {dev_score}")

        # Create a team
        print("\n👥 Creating team...")
        team_name = "python_team"
        await scoreboard.createTeam(team_name)
        await scoreboard.setTeamDisplayName(team_name, "Python Developers")
        await scoreboard.setTeamColor(team_name, "AQUA")
        await scoreboard.setTeamPrefix(team_name, "[DEV] ")
        print(f"✅ Created team: {team_name}")

        # Add player to team
        print(f"\n👤 Adding Dev to team...")
        await scoreboard.addPlayerToTeam(team_name, "Dev")
        print(f"✅ Dev added to Python Developers team")

        # Get team info
        team_info = await scoreboard.getTeam(team_name)
        print(f"\n📋 Team Info:")
        print(f"  Name: {team_info.displayName}")
        print(f"  Color: {team_info.color}")
        print(f"  Prefix: {team_info.prefix}")
        print(f"  Members: {', '.join(team_info.players)}")

        print("\n✅ Scoreboard setup complete!")
        await player.sendMessage("Check the sidebar for your score!")


if __name__ == "__main__":
    asyncio.run(main())
