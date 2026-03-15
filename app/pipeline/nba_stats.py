import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from nba_api.stats.endpoints import playergamelog, leaguegamefinder
from nba_api.stats.static import players, teams
from app.models.database import SessionLocal, PlayerGame, Game
import pandas as pd
import time

def get_all_players():
    return players.get_active_players()

def load_player_games(player_name, season="2024-25", max_games=100):
    db = SessionLocal()
    
    try:
        all_players = players.get_active_players()
        matches = [p for p in all_players if player_name.lower() in p["full_name"].lower()]
        
        if not matches:
            print(f"Player {player_name} not found")
            return
        
        player = matches[0]
        print(f"Loading stats for {player['full_name']}...")
        
        gamelog = playergamelog.PlayerGameLog(
            player_id=player["id"],
            season=season
        )
        
        df = gamelog.get_data_frames()[0]
        print(f"Found {len(df)} games")
        
        for _, row in df.head(max_games).iterrows():
            game_id = f"nba_{row['Game_ID']}"
            player_game_id = f"{game_id}_{player['id']}"
            
            existing = db.query(PlayerGame).filter(PlayerGame.id == player_game_id).first()
            if existing:
                continue
            
            pts = float(row.get("PTS", 0) or 0)
            reb = float(row.get("REB", 0) or 0)
            ast = float(row.get("AST", 0) or 0)
            stl = float(row.get("STL", 0) or 0)
            blk = float(row.get("BLK", 0) or 0)
            tov = float(row.get("TOV", 0) or 0)
            fantasy = (pts * 1.0) + (reb * 1.2) + (ast * 1.5) + (stl * 3.0) + (blk * 3.0) - (tov * 1.0)
            
            pg = PlayerGame(
                id=player_game_id,
                game_id=game_id,
                player_id=str(player["id"]),
                player_name=player["full_name"],
                team=row.get("MATCHUP", "").split(" ")[0],
                points=pts,
                rebounds=reb,
                assists=ast,
                minutes=float(str(row.get("MIN", 0)).split(":")[0] or 0),
                fg_percentage=float(row.get("FG_PCT", 0) or 0) * 100,
                three_point_percentage=float(row.get("FG3_PCT", 0) or 0) * 100,
                usage_rate=0.0,
                fantasy_points=fantasy
            )
            db.add(pg)
        
        db.commit()
        print(f"Saved stats for {player['full_name']}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    stars = [
        "LeBron James",
        "Stephen Curry", 
        "Jayson Tatum",
        "Giannis Antetokounmpo",
        "Luka Doncic",
        "Kevin Durant",
        "Anthony Davis",
        "Nikola Jokić"
    ]
    
    for player in stars:
        load_player_games(player)
        time.sleep(1)
    
    print("\nAll done! Checking database...")
    db = SessionLocal()
    count = db.query(PlayerGame).count()
    print(f"Total player game records: {count}")
    db.close()
