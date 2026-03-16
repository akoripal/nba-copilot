# 🏀 NBA AI Copilot

> An AI-powered NBA fantasy performance predictor combining machine learning, explainability, and natural language analysis.

**Live Demo:** https://nba-copilot.vercel.app  
**API:** https://nba-copilot.onrender.com/docs  
**GitHub:** https://github.com/akoripal/nba-copilot

---

## What It Does

Given a player and opponent, the system:
1. Pulls their recent performance features from a PostgreSQL database
2. Runs an XGBoost model to predict fantasy point output
3. Uses SHAP to identify the top drivers of the prediction
4. Passes those drivers to Groq (Llama 3.3) to generate plain-English analyst commentary

**Example output for Anthony Edwards vs OKC Thunder:**
- Predicted: 44.2 fantasy points
- AI Analysis: *"Edwards is poised for a strong outing driven by his 10-game fantasy average of 44.6. However, facing OKC's elite defense (106.3 rating) on the road on a back-to-back may temper his output slightly..."*

---

## Model Performance

| Metric | Value |
|--------|-------|
| MAE | ±8.25 fantasy points |
| R² | 0.495 |
| Within 10 pts | 68% |
| Within 15 pts | 86.5% |
| Training samples | 13,000+ player-game records |
| Players | 150+ across 2 seasons |

---

## Architecture
```
NBA Stats API + Sportradar
        ↓
   ETL Pipeline (Python)
        ↓
  PostgreSQL Database
        ↓
 Feature Engineering
 (19 predictive signals)
        ↓
  XGBoost Model
        ↓
  SHAP Explainer
        ↓
  Groq LLM Layer
  (Llama 3.3 70B)
        ↓
  FastAPI Backend
        ↓
  Next.js Dashboard
```

---

## Features Engineered

| Feature | Description |
|---------|-------------|
| `roll5_points` | Rolling 5-game points average |
| `roll10_fantasy` | Rolling 10-game fantasy average |
| `pts_trend` | Last 5 vs last 10 average delta |
| `pts_consistency` | Rolling standard deviation |
| `minutes_trend` | 3-game minutes rolling average |
| `opp_def_rating` | Real opponent defensive rating |
| `is_back_to_back` | Back-to-back game flag |
| `vs_season_avg` | Recent form vs season average |
| `is_star_player` | High usage player flag |
| `roll5_efficiency` | Points per minute rolling average |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Data | NBA Stats API, Sportradar, Python, Pandas |
| Database | PostgreSQL, SQLAlchemy, Alembic |
| ML | XGBoost, SHAP, scikit-learn, MLflow |
| AI | Groq API (Llama 3.3 70B) |
| Backend | FastAPI, Uvicorn, Pydantic |
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Deployment | Render (API), Vercel (Frontend) |

---

## API Endpoints
```
POST /predict          # Generate prediction + AI analysis
GET  /players          # List all 2025-26 season players
GET  /player/{name}    # Get player stats summary
GET  /health           # Health check
```

**Example request:**
```json
POST /predict
{
  "player_name": "Scottie Barnes",
  "opponent_team": "Pistons",
  "is_home": 1
}
```

**Example response:**
```json
{
  "player_name": "Scottie Barnes",
  "predicted_fantasy_points": 34.5,
  "roll5_points_avg": 18.2,
  "roll10_fantasy_avg": 32.8,
  "opponent_def_rating": 108.8,
  "ai_analysis": "Scottie Barnes is poised for a strong outing..."
}
```

---

## Local Setup
```bash
# Clone the repo
git clone https://github.com/akoripal/nba-copilot.git
cd nba-copilot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Add your GROQ_API_KEY and SPORTRADAR_API_KEY

# Create database
createdb nba_copilot

# Load data
python app/pipeline/nba_stats.py

# Train model
python app/ml/model.py

# Start API
uvicorn app.api.main:app --reload --port 8000

# Start frontend (new terminal)
cd frontend && npm run dev
```

---

## Key Technical Decisions

**Why XGBoost over a neural network?**  
Tabular sports data with ~100 features responds better to gradient boosting. XGBoost trained in seconds vs minutes, achieved lower MAE, and SHAP explainability works natively with tree models.

**Why SHAP + LLM instead of just an LLM?**  
The LLM is not the prediction engine — it's the voice. XGBoost predicts, SHAP identifies the top 5 feature drivers, and Groq turns those drivers into readable analyst commentary. This prevents hallucination and grounds every explanation in model output.

**Why Groq over OpenAI?**  
Free tier covers the use case, response times are faster due to custom hardware, and Llama 3.3 70B is sufficient for structured explanation tasks.

---

## Author

Anurag Koripalli  
[GitHub](https://github.com/akoripal)

---

*Built as a portfolio project demonstrating end-to-end AI engineering — data pipelines, ML modeling, explainability, LLM integration, and full-stack deployment.*