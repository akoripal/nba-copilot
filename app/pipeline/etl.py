import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.pipeline.sportradar import get_schedule, get_game_boxscore
from app.models.database import SessionLocal, Game, PlayerGame
from datetime import datetime
import time

def parse_minutes(minutes_str):
    try:
        if ":" in str(minutes_str):
            parts = str(minutes_str).split(":")
            return float(parts[0]) + float(parts[1]) / 60
        return float(minutes_str or 0)
    except:
        return 0.0

def calculate_fantasy_points(stats):
    pts = stats.get("points", 0) or 0
    reb = stats.get("rebounds", 0) or 0
    ast = stats.get("assists", 0) or 0
    stl = stats.get("steals", 0) or 0
    blk = stats.get("blocks", 0) or 0
    tov = stats.get("turnovers", 0) or 0
    return (pts * 1.0) + (reb * 1.2) + (ast * 1.5) + (stl * 3.0) + (blk * 3.0) - (tov * 1.0)

def extract_players(team_data):
    players = []
    # Try direct players list
    if "players" in team_data:
        players = team_data["players"]
    # Try roster
    elif "roster" in team_data:
        players = team_data["roster"]
    # Try leaders (limited data)
    elif "leaders" in team_data:
        for category in team_data["leaders"].values():
            if isinstance(category, list):
                for p in category:
                    if p not in players:
                        players.append(p)
    return players

def load_games(season_year="2024", max_games=50):
    print(f"Fetching schedule for {season_year}...")
    schedule = get_schedule(season_year)

    if not schedule:
        print("Failed to fetch schedule")
        return

    games = schedule.get("games", [])
    completed = [g for g in games if g.get("status") == "closed"]
    print(f"Found {len(completed)} completed games, loading {min(max_games, len(completed))}...")

    db = SessionLocal()
    games_loaded = 0

    for game in completed[:max_games]:
        try:
            game_id = game["id"]

            existing = db.query(Game).filter(Game.id == game_id).first()
            if existing:
                print(f"Skipping already loaded game {game_id}")
                continue

            scheduled = game.get("scheduled", "")
            game_date = datetime.fromisoformat(scheduled.replace("Z", "+00:00")).date() if scheduled else None

            db_game = Game(
                id=game_id,
                date=game_date,
                home_team=game.get("home", {}).get("name", ""),
                away_team=game.get("away", {}).get("name", ""),
                home_score=game.get("home_points", 0),
                away_score=game.get("away_points", 0),
                season=season_year
            )
            db.add(db_game)

            print(f"Loading boxscore: {db_game.away_team} @ {db_game.home_team}...")
            boxscore = get_game_boxscore(game_id)
            time.sleep(1)

            if boxscore:
                players_saved = 0
                for team_type in ["home", "away"]:
                    team_data = boxscore.get(team_type, {})
                    team_name = team_data.get("name", "")
                    players = extract_players(team_data)

                    for player in players:
                        stats = player.get("statistics", {})
                        if not stats:
                            continue

                        pg = PlayerGame(
                            id=f"{game_id}_{player['id']}",
                            game_id=game_id,
                            player_id=player["id"],
                            player_name=player.get("full_name", ""),
                            team=team_name,
                            points=stats.get("points", 0) or 0,
                            rebounds=stats.get("rebounds", 0) or 0,
                            assists=stats.get("assists", 0) or 0,
                            minutes=parse_minutes(stats.get("minutes", 0)),
                            fg_percentage=stats.get("field_goals_pct", 0) or 0,
                            three_point_percentage=stats.get("three_points_pct", 0) or 0,
                            usage_rate=0.0,
                            fantasy_points=calculate_fantasy_points(stats)
                        )
                        db.add(pg)
                        players_saved += 1

                print(f"Saved {players_saved} player records")

            db.commit()
            games_loaded += 1

        except Exception as e:
            print(f"Error processing game: {e}")
            db.rollback()
            continue

    db.close()
    print(f"\nDone! Loaded {games_loaded} games into the database.")

if __name__ == "__main__":
    load_games(max_games=25)
    