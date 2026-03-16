import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pickle
import shap
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")

app = FastAPI(
    title="NBA AI Copilot API",
    description="Predict NBA player fantasy performance with AI explanations",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Loading model artifacts...")
with open("app/ml/saved/model.pkl", "rb") as f:
    model = pickle.load(f)
with open("app/ml/saved/feature_cols.pkl", "rb") as f:
    feature_cols = pickle.load(f)

# Recreate explainer from model instead of loading pickle
# This avoids numba/Python version compatibility issues
explainer = shap.TreeExplainer(model)
print("Model loaded!")

class PredictionRequest(BaseModel):
    player_name: str
    opponent_team: str
    is_home: Optional[int] = 0

class PredictionResponse(BaseModel):
    player_name: str
    opponent_team: str
    predicted_fantasy_points: float
    roll5_points_avg: float
    roll10_fantasy_avg: float
    points_trend: float
    opponent_def_rating: float
    is_home: int
    ai_analysis: str
    model_version: str = "xgboost-v2"

class PlayerStatsResponse(BaseModel):
    player_name: str
    games_in_database: int
    avg_fantasy_points: float
    avg_points: float
    avg_rebounds: float
    avg_assists: float
    best_game: float
    worst_game: float
    consistency_score: float

@app.get("/")
def root():
    return {
        "message": "NBA AI Copilot API",
        "version": "1.0.0",
        "endpoints": [
            "/predict",
            "/players",
            "/player/{player_name}",
            "/health"
        ]
    }

@app.get("/health")
def health():
    return {"status": "healthy", "model": "loaded"}

@app.get("/players")
def get_all_players():
    try:
        from app.models.database import SessionLocal, PlayerGame
        db = SessionLocal()
        records = db.query(PlayerGame.player_name, PlayerGame.game_id).all()
        db.close()

        current_season_players = set()
        for name, game_id in records:
            if game_id and game_id.startswith("nba_002250"):
                current_season_players.add(name)

        print(f"2025-26 players found: {len(current_season_players)}")

        if len(current_season_players) < 10:
            current_season_players = {r[0] for r in records}

        players = sorted(list(current_season_players))
        return {"players": players, "count": len(players)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    try:
        from app.ml.explainer import predict_and_explain
        predicted_fp, explanation = predict_and_explain(
            player_name=request.player_name,
            opp_team_name=request.opponent_team,
            is_home=request.is_home
        )

        from app.ml.features import build_features
        from app.models.database import SessionLocal, Team

        df = build_features().reset_index(drop=True)
        player_df = df[df["player_name"].str.contains(
            request.player_name.split()[0], case=False
        )]

        if player_df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Player {request.player_name} not found"
            )

        db = SessionLocal()
        opp = db.query(Team).filter(
            Team.name.contains(request.opponent_team)
        ).first()
        db.close()

        latest = player_df.iloc[-1]

        return PredictionResponse(
            player_name=request.player_name,
            opponent_team=request.opponent_team,
            predicted_fantasy_points=round(float(predicted_fp), 1),
            roll5_points_avg=round(float(latest["roll5_points"]), 1),
            roll10_fantasy_avg=round(float(latest["roll10_fantasy"]), 1),
            points_trend=round(float(latest["pts_trend"]), 1),
            opponent_def_rating=round(float(opp.defensive_rating if opp else 115.0), 1),
            is_home=request.is_home,
            ai_analysis=explanation
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{player_name}", response_model=PlayerStatsResponse)
def get_player_stats(player_name: str):
    try:
        from app.ml.features import build_features

        df = build_features().reset_index(drop=True)
        player_df = df[df["player_name"].str.contains(
            player_name.split()[0], case=False
        )]

        if player_df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Player {player_name} not found in database"
            )

        name = player_df["player_name"].iloc[0]

        return PlayerStatsResponse(
            player_name=name,
            games_in_database=len(player_df),
            avg_fantasy_points=round(float(player_df["fantasy"].mean()), 1),
            avg_points=round(float(player_df["points"].mean()), 1),
            avg_rebounds=round(float(player_df["roll5_rebounds"].mean()), 1),
            avg_assists=round(float(player_df["roll5_assists"].mean()), 1),
            best_game=round(float(player_df["fantasy"].max()), 1),
            worst_game=round(float(player_df["fantasy"].min()), 1),
            consistency_score=round(float(player_df["pts_consistency"].mean()), 2)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))