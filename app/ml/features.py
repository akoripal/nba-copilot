import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.models.database import SessionLocal, PlayerGame, Team
import pandas as pd
import numpy as np

def get_team_defensive_ratings():
    db = SessionLocal()
    teams = db.query(Team).all()
    db.close()
    
    ratings = {t.name: t.defensive_rating for t in teams if t.defensive_rating}
    
    if not ratings:
        return {
            'Golden State Warriors': 108.2, 'Boston Celtics': 109.1,
            'Memphis Grizzlies': 109.8, 'Milwaukee Bucks': 110.2,
            'Miami Heat': 110.5, 'Cleveland Cavaliers': 110.8,
            'New York Knicks': 111.2, 'Minnesota Timberwolves': 111.5,
            'Los Angeles Lakers': 112.1, 'Phoenix Suns': 112.4,
            'Dallas Mavericks': 112.8, 'Denver Nuggets': 113.1,
            'Philadelphia 76ers': 113.4, 'Sacramento Kings': 113.8,
            'Atlanta Hawks': 114.2, 'Chicago Bulls': 114.5,
            'Brooklyn Nets': 115.1, 'Toronto Raptors': 115.4,
            'Orlando Magic': 115.8, 'Indiana Pacers': 116.2,
            'Oklahoma City Thunder': 116.5, 'New Orleans Pelicans': 116.8,
            'Los Angeles Clippers': 117.1, 'Utah Jazz': 117.5,
            'San Antonio Spurs': 118.2, 'Washington Wizards': 118.8,
            'Detroit Pistons': 119.2, 'Charlotte Hornets': 119.8,
            'Portland Trail Blazers': 120.1, 'Houston Rockets': 120.5,
        }
    
    return ratings

def build_features():
    print("Loading data from database...")
    db = SessionLocal()
    records = db.query(PlayerGame).all()
    db.close()

    df = pd.DataFrame([{
        "player_id":   r.player_id,
        "player_name": r.player_name,
        "game_id":     r.game_id,
        "team":        r.team,
        "points":      r.points,
        "rebounds":    r.rebounds,
        "assists":     r.assists,
        "minutes":     r.minutes,
        "fg_pct":      r.fg_percentage,
        "three_pct":   r.three_point_percentage,
        "fantasy":     r.fantasy_points,
    } for r in records])

    print(f"Loaded {len(df)} records for {df['player_name'].nunique()} players")

    df = df.sort_values(["player_id", "game_id"]).reset_index(drop=True)

    # ── FEATURE 1: Rolling 5-game averages ──
    print("Building rolling averages...")
    for col in ["points", "rebounds", "assists", "minutes", "fantasy"]:
        df[f"roll5_{col}"] = (
            df.groupby("player_id")[col]
            .transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
            .round(2)
        )

    # ── FEATURE 2: Rolling 10-game averages ──
    for col in ["points", "fantasy"]:
        df[f"roll10_{col}"] = (
            df.groupby("player_id")[col]
            .transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
            .round(2)
        )

    # ── FEATURE 3: Home / away ──
    print("Building home/away features...")
    df["is_home"] = df["team"].apply(lambda x: 1 if "@" not in str(x) else 0)

    # ── FEATURE 4: Trend features ──
    print("Building trend features...")
    df["pts_trend"] = (df["roll5_points"] - df["roll10_points"]).round(2)
    df["fantasy_trend"] = (df["roll5_fantasy"] - df["roll10_fantasy"]).round(2)

    # ── FEATURE 5: Consistency ──
    df["pts_consistency"] = (
        df.groupby("player_id")["points"]
        .transform(lambda x: x.shift(1).rolling(5, min_periods=2).std())
        .round(2)
    )

    # ── FEATURE 6: Minutes trend ──
    df["minutes_trend"] = (
        df.groupby("player_id")["minutes"]
        .transform(lambda x: x.shift(1).rolling(3, min_periods=1).mean())
        .round(2)
    )

    # ── FEATURE 7: Scoring efficiency ──
    df["pts_per_minute"] = (df["points"] / df["minutes"].replace(0, 1)).round(3)
    df["roll5_efficiency"] = (
        df.groupby("player_id")["pts_per_minute"]
        .transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
        .round(3)
    )

    # ── FEATURE 8: Real opponent defensive rating ──
    print("Loading real opponent defensive ratings from database...")
    def_ratings = get_team_defensive_ratings()
    print(f"Loaded ratings for {len(def_ratings)} teams")
    df["opp_def_rating"] = df["team"].map(
        lambda x: def_ratings.get(str(x), 115.0)
    )

    # ── FEATURE 9: Back to back ──
    print("Building rest days feature...")
    df["game_number"] = df.groupby("player_id").cumcount()
    df["games_per_stretch"] = (
        df.groupby("player_id")["game_number"]
        .transform(lambda x: x.diff().fillna(1))
    )
    df["is_back_to_back"] = (df["games_per_stretch"] == 1).astype(int)

    # ── FEATURE 10: Season average vs recent form ──
    print("Building season average features...")
    df["season_avg_pts"] = (
        df.groupby("player_id")["points"]
        .transform(lambda x: x.expanding().mean().shift(1))
        .round(2)
    )
    df["vs_season_avg"] = (df["roll5_points"] - df["season_avg_pts"]).round(2)

    # ── FEATURE 11: Star player flag ──
    df["is_star_player"] = (df["season_avg_pts"] > 20).astype(int)

    # ── FEATURE 12: Defensive rating vs player average ──
    # Higher = easier matchup, lower = harder matchup
    player_avg_opp = (
        df.groupby("player_id")["opp_def_rating"]
        .transform(lambda x: x.shift(1).expanding().mean())
        .round(2)
    )
    df["def_rating_vs_avg"] = (df["opp_def_rating"] - player_avg_opp).round(2)

    feature_cols = [
        "player_id", "player_name", "game_id",
        "points", "fantasy",
        "roll5_points", "roll5_rebounds", "roll5_assists",
        "roll5_minutes", "roll5_fantasy",
        "roll10_points", "roll10_fantasy",
        "pts_trend", "fantasy_trend",
        "pts_consistency", "minutes_trend",
        "roll5_efficiency", "is_home",
        "opp_def_rating", "is_back_to_back",
        "vs_season_avg", "is_star_player",
        "def_rating_vs_avg"
    ]

    df_features = df[feature_cols].dropna()
    print(f"\nFeature matrix shape: {df_features.shape}")
    print(f"Features built: {len(feature_cols) - 4} predictive features")
    print(f"\nSample — {df_features['player_name'].iloc[0]}:")
    print(df_features.iloc[0][["roll5_points", "opp_def_rating", "def_rating_vs_avg", "is_back_to_back"]].to_string())

    return df_features

if __name__ == "__main__":
    df = build_features()
    print("\n✅ Feature engineering complete!")
    print(df[["player_name", "roll5_points", "opp_def_rating", "def_rating_vs_avg", "fantasy"]].head(10).to_string(index=False))