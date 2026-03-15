'use client'

import { useState } from 'react'

interface PredictionResult {
  player_name: string
  opponent_team: string
  predicted_fantasy_points: number
  roll5_points_avg: number
  roll10_fantasy_avg: number
  points_trend: number
  opponent_def_rating: number
  is_home: number
  ai_analysis: string
}

export default function Home() {
  const [playerName, setPlayerName] = useState('')
  const [opponent, setOpponent] = useState('')
  const [isHome, setIsHome] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<PredictionResult | null>(null)
  const [error, setError] = useState('')

  const handlePredict = async () => {
    if (!playerName || !opponent) {
      setError('Please enter both a player name and opponent team')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await fetch('http://localhost:8000/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_name: playerName,
          opponent_team: opponent,
          is_home: isHome ? 1 : 0
        })
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Prediction failed')
      }

      const data = await response.json()
      setResult(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const getTrendColor = (trend: number) => {
    if (trend > 2) return 'text-green-400'
    if (trend < -2) return 'text-red-400'
    return 'text-yellow-400'
  }

  const getDefRatingLabel = (rating: number) => {
    if (rating < 108) return { label: 'Elite Defense', color: 'text-red-400' }
    if (rating < 112) return { label: 'Good Defense', color: 'text-orange-400' }
    if (rating < 116) return { label: 'Average Defense', color: 'text-yellow-400' }
    return { label: 'Weak Defense', color: 'text-green-400' }
  }

  return (
    <main className="min-h-screen bg-gray-950 text-white">

      {/* Header */}
      <div className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center gap-3">
          <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center text-sm font-bold">
            🏀
          </div>
          <div>
            <h1 className="text-lg font-bold">NBA AI Copilot</h1>
            <p className="text-xs text-gray-400">XGBoost + SHAP + Groq — Fantasy Performance Predictor</p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-xs text-gray-400">API Live</span>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-8">

        {/* Input Card */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6">
          <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-4">
            Generate Prediction
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Player Name</label>
              <input
                type="text"
                value={playerName}
                onChange={(e) => setPlayerName(e.target.value)}
                placeholder="e.g. Scottie Barnes"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-orange-500 transition-colors"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Opponent Team</label>
              <input
                type="text"
                value={opponent}
                onChange={(e) => setOpponent(e.target.value)}
                placeholder="e.g. Pistons"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-orange-500 transition-colors"
              />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 cursor-pointer">
              <div
                onClick={() => setIsHome(!isHome)}
                className={`w-10 h-5 rounded-full transition-colors ${isHome ? 'bg-orange-500' : 'bg-gray-700'} relative`}
              >
                <div className={`w-4 h-4 bg-white rounded-full absolute top-0.5 transition-transform ${isHome ? 'translate-x-5' : 'translate-x-0.5'}`}></div>
              </div>
              <span className="text-sm text-gray-400">Home game</span>
            </label>

            <button
              onClick={handlePredict}
              disabled={loading}
              className="bg-orange-500 hover:bg-orange-600 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium px-6 py-3 rounded-lg text-sm transition-colors"
            >
              {loading ? 'Analyzing...' : 'Generate Prediction →'}
            </button>
          </div>

          {error && (
            <div className="mt-4 bg-red-900/30 border border-red-800 rounded-lg px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
            <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
            <p className="text-gray-400 text-sm">Running XGBoost model + SHAP analysis + Groq LLM...</p>
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <div className="space-y-4">

            {/* Main prediction */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold">{result.player_name}</h2>
                  <p className="text-gray-400 text-sm mt-1">
                    vs {result.opponent_team} · {result.is_home ? 'Home' : 'Away'}
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-4xl font-bold text-orange-400">
                    {result.predicted_fantasy_points}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Predicted Fantasy Pts</div>
                </div>
              </div>

              {/* Stats grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-gray-800 rounded-lg p-3">
                  <div className="text-xs text-gray-500 mb-1">Roll5 Pts Avg</div>
                  <div className="text-lg font-semibold">{result.roll5_points_avg}</div>
                </div>
                <div className="bg-gray-800 rounded-lg p-3">
                  <div className="text-xs text-gray-500 mb-1">Roll10 Fantasy</div>
                  <div className="text-lg font-semibold">{result.roll10_fantasy_avg}</div>
                </div>
                <div className="bg-gray-800 rounded-lg p-3">
                  <div className="text-xs text-gray-500 mb-1">Points Trend</div>
                  <div className={`text-lg font-semibold ${getTrendColor(result.points_trend)}`}>
                    {result.points_trend > 0 ? '+' : ''}{result.points_trend}
                  </div>
                </div>
                <div className="bg-gray-800 rounded-lg p-3">
                  <div className="text-xs text-gray-500 mb-1">Opp Def Rating</div>
                  <div className={`text-lg font-semibold ${getDefRatingLabel(result.opponent_def_rating).color}`}>
                    {result.opponent_def_rating}
                  </div>
                  <div className={`text-xs ${getDefRatingLabel(result.opponent_def_rating).color}`}>
                    {getDefRatingLabel(result.opponent_def_rating).label}
                  </div>
                </div>
              </div>
            </div>

            {/* AI Analysis */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-5 h-5 bg-purple-500/20 rounded flex items-center justify-center text-xs">✦</div>
                <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">AI Analysis</h3>
                <span className="ml-auto text-xs text-gray-600 bg-gray-800 px-2 py-1 rounded">Groq · Llama 3.3</span>
              </div>
              <p className="text-gray-200 leading-relaxed text-sm">{result.ai_analysis}</p>
            </div>

            {/* Model info */}
            <div className="flex items-center gap-4 text-xs text-gray-600 px-1">
              <span>Model: XGBoost v2</span>
              <span>·</span>
              <span>Features: 19 predictive signals</span>
              <span>·</span>
              <span>MAE: ±8.25 fantasy pts</span>
              <span>·</span>
              <span>Within 10pts: 68%</span>
            </div>

          </div>
        )}

        {/* Empty state */}
        {!result && !loading && (
          <div className="bg-gray-900 border border-dashed border-gray-800 rounded-xl p-12 text-center">
            <div className="text-4xl mb-3">🏀</div>
            <p className="text-gray-500 text-sm">Enter a player and opponent to generate a prediction</p>
            <p className="text-gray-600 text-xs mt-2">Try: Scottie Barnes vs Pistons</p>
          </div>
        )}

      </div>
    </main>
  )
}