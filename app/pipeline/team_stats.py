import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from nba_api.stats.endpoints import leaguedashteamstats
from app.models.database import SessionLocal, Team
import time

def load_team_defensive_ratings(season="2024-25"):
    print(f"Loading real team defensive ratings for {season}...")
    
    stats = leaguedashteamstats.LeagueDashTeamStats(
        season=season,
        measure_type_detailed_defense="Defense",
        per_mode_detailed="PerGame"
    )
    
    df = stats.get_data_frames()[0]
    
    ratings = {}
    for _, row in df.iterrows():
        team_name = row["TEAM_NAME"]
        def_rating = row.get("DEF_RATING", 115.0)
        ratings[team_name] = round(float(def_rating), 2)
    
    print(f"Loaded defensive ratings for {len(ratings)} teams")
    for team, rating in sorted(ratings.items(), key=lambda x: x[1]):
        print(f"  {team:<30} {rating}")
    
    return ratings

def save_team_ratings(season="2024-25"):
    db = SessionLocal()
    ratings = load_team_defensive_ratings(season)
    
    for name, def_rating in ratings.items():
        existing = db.query(Team).filter(Team.name == name).first()
        if existing:
            existing.defensive_rating = def_rating
        else:
            team = Team(
                id=name.lower().replace(" ", "_"),
                name=name,
                abbreviation="",
                defensive_rating=def_rating,
                pace=0.0,
                offensive_rating=0.0
            )
            db.add(team)
    
    db.commit()
    db.close()
    print(f"\nSaved {len(ratings)} team ratings to database!")
    return ratings

if __name__ == "__main__":
    for season in ["2024-25", "2025-26"]:
        save_team_ratings(season)
        time.sleep(1)