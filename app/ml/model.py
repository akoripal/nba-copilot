import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.ml.features import build_features
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_absolute_error, r2_score
import mlflow
import mlflow.xgboost
import shap
import pickle

def train_model():
    print("Building feature matrix...")
    df = build_features()

    feature_cols = [
        "roll5_points", "roll5_rebounds", "roll5_assists",
        "roll5_minutes", "roll5_fantasy",
        "roll10_points", "roll10_fantasy",
        "pts_trend", "fantasy_trend",
        "pts_consistency", "minutes_trend",
        "roll5_efficiency", "is_home",
        "opp_def_rating", "is_back_to_back",
        "vs_season_avg", "is_star_player"
    ]

    X = df[feature_cols]
    y = df["fantasy"]

    print(f"Training on {len(X)} samples with {len(feature_cols)} features")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"Train: {len(X_train)} | Test: {len(X_test)}")

    # ── Hyperparameter tuning ──
    print("\nRunning hyperparameter search...")
    param_grid = {
        "n_estimators":     [200, 300, 500],
        "max_depth":        [3, 4, 6],
        "learning_rate":    [0.01, 0.05, 0.1],
        "subsample":        [0.8, 1.0],
        "colsample_bytree": [0.8, 1.0],
    }

    base_model = xgb.XGBRegressor(random_state=42, verbosity=0)
    grid_search = GridSearchCV(
        base_model,
        param_grid,
        cv=5,
        scoring="neg_mean_absolute_error",
        n_jobs=-1,
        verbose=1
    )
    grid_search.fit(X_train, y_train)

    best_params = grid_search.best_params_
    print(f"\nBest params: {best_params}")

    mlflow.set_experiment("nba_fantasy_prediction_v2")

    with mlflow.start_run():
        model = xgb.XGBRegressor(**best_params, random_state=42, verbosity=0)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        mae  = mean_absolute_error(y_test, y_pred)
        r2   = r2_score(y_test, y_pred)

        # Accuracy metrics
        within_10 = np.mean(np.abs(y_pred - y_test.values) <= 10) * 100
        within_15 = np.mean(np.abs(y_pred - y_test.values) <= 15) * 100

        print(f"\n{'='*45}")
        print(f"  MAE          : {mae:.2f} fantasy points")
        print(f"  R²           : {r2:.3f}")
        print(f"  Within 10pts : {within_10:.1f}%")
        print(f"  Within 15pts : {within_15:.1f}%")
        print(f"{'='*45}")

        mlflow.log_params(best_params)
        mlflow.log_metric("mae", mae)
        mlflow.log_metric("r2", r2)
        mlflow.log_metric("within_10_pct", within_10)
        mlflow.xgboost.log_model(model, "model")

        # SHAP
        print("\nCalculating SHAP values...")
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test)

        shap_df = pd.DataFrame(
            np.abs(shap_values), columns=feature_cols
        ).mean().sort_values(ascending=False)

        print("\nTop features by importance (SHAP):")
        print("-"*40)
        for feat, val in shap_df.head(10).items():
            bar = "█" * int(val / shap_df.max() * 20)
            print(f"  {feat:<25} {bar} {val:.3f}")

        os.makedirs("app/ml/saved", exist_ok=True)
        with open("app/ml/saved/model.pkl", "wb") as f:
            pickle.dump(model, f)
        with open("app/ml/saved/explainer.pkl", "wb") as f:
            pickle.dump(explainer, f)
        with open("app/ml/saved/feature_cols.pkl", "wb") as f:
            pickle.dump(feature_cols, f)

        print(f"\n✅ Model saved!")
        print(f"\nResume bullet: XGBoost model predicting NBA fantasy output with MAE ±{mae:.1f} pts, {within_10:.0f}% within 10 points")

    return model, explainer, feature_cols

if __name__ == "__main__":
    train_model()
    
    
