import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from groq import Groq
from dotenv import load_dotenv
import pickle
import numpy as np
import shap

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def load_model_artifacts():
    with open("app/ml/saved/model.pkl", "rb") as f:
        model = pickle.load(f)
    with open("app/ml/saved/explainer.pkl", "rb") as f:
        explainer = pickle.load(f)
    with open("app/ml/saved/feature_cols.pkl", "rb") as f:
        feature_cols = pickle.load(f)
    return model, explainer, feature_cols

def get_shap_explanation(explainer, feature_cols, X_row):
    shap_values = explainer.shap_values(X_row)
    shap_dict = dict(zip(feature_cols, shap_values[0]))
    sorted_shap = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)
    return sorted_shap[:5]

def generate_explanation(player_name, predicted_fp, top_shap, player_stats):
    roll5_pts    = round(player_stats.get("roll5_points", 0), 1)
    roll10_fp    = round(player_stats.get("roll10_fantasy", 0), 1)
    trend        = round(player_stats.get("pts_trend", 0), 1)
    consistency  = round(player_stats.get("pts_consistency", 0), 1)
    opp_rating   = round(player_stats.get("opp_def_rating", 115.0), 1)
    is_home      = player_stats.get("is_home", 0)
    back_to_back = player_stats.get("is_back_to_back", 0)

    shap_text = "\n".join([
        f"- {feat}: {'+' if val > 0 else ''}{round(val, 2)} impact"
        for feat, val in top_shap
    ])

    prompt = f"""
You are an expert NBA fantasy sports analyst. Based on the following model output, 
write a concise 3-4 sentence analysis explaining the prediction. 
Be specific, confident, and use basketball terminology. 
Do NOT mention SHAP or machine learning — write as if you are a human analyst.

Player: {player_name}
Predicted fantasy points: {predicted_fp}

Key stats:
- Last 5 game points average: {roll5_pts}
- Last 10 game fantasy average: {roll10_fp}
- Points trend (last 5 vs last 10): {'+' + str(trend) if trend > 0 else str(trend)}
- Consistency score (lower = more consistent): {consistency}
- Opponent defensive rating: {opp_rating} (lower = tougher defense)
- Playing at home: {'Yes' if is_home else 'No'}
- Back to back game: {'Yes' if back_to_back else 'No'}

Top factors driving this prediction:
{shap_text}

Write a 3-4 sentence analyst commentary explaining why {player_name} 
is projected for {predicted_fp} fantasy points tonight.
Keep it punchy and specific. End with a confidence statement.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=200
    )

    return response.choices[0].message.content.strip()

def predict_and_explain(player_name, opp_team_name="opponent", is_home=0):
    from app.ml.features import build_features
    from app.models.database import SessionLocal, Team

    model, explainer, feature_cols = load_model_artifacts()
    df = build_features().reset_index(drop=True)

    player_df = df[df["player_name"].str.contains(
        player_name.split()[0], case=False
    )]

    if player_df.empty:
        print(f"No data found for {player_name}")
        return

    db = SessionLocal()
    opp = db.query(Team).filter(
        Team.name.contains(opp_team_name)
    ).first()
    db.close()

    opp_rating = opp.defensive_rating if opp else 115.0

    latest = player_df.iloc[-1][feature_cols].copy()
    latest["opp_def_rating"] = opp_rating
    latest["is_home"] = is_home

    X = latest.values.reshape(1, -1)
    predicted_fp = round(model.predict(X)[0], 1)

    top_shap = get_shap_explanation(explainer, feature_cols, X)

    player_stats = {
        "roll5_points":    player_df.iloc[-1]["roll5_points"],
        "roll10_fantasy":  player_df.iloc[-1]["roll10_fantasy"],
        "pts_trend":       player_df.iloc[-1]["pts_trend"],
        "pts_consistency": player_df.iloc[-1]["pts_consistency"],
        "opp_def_rating":  opp_rating,
        "is_home":         is_home,
        "is_back_to_back": player_df.iloc[-1]["is_back_to_back"],
    }

    explanation = generate_explanation(
        player_name, predicted_fp, top_shap, player_stats
    )

    print()
    print("=" * 55)
    print(f"  {player_name} vs {opp_team_name}")
    print("=" * 55)
    print(f"  Predicted fantasy points : {predicted_fp}")
    print(f"  Roll5 points avg         : {round(player_stats['roll5_points'], 1)}")
    print(f"  Roll10 fantasy avg       : {round(player_stats['roll10_fantasy'], 1)}")
    print(f"  Opponent def rating      : {opp_rating}")
    print("-" * 55)
    print("  AI ANALYSIS:")
    print()
    print(f"  {explanation}")
    print("=" * 55)

    return predicted_fp, explanation

if __name__ == "__main__":
    predict_and_explain(
        player_name="Anthony Edwards",
        opp_team_name="Thunder",
        is_home=0
    )
