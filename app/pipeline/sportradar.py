import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SPORTRADAR_API_KEY")
BASE_URL = "https://api.sportradar.com/nba/trial/v8/en"

def get_schedule(season_year="2024", season_type="REG"):
    url = f"{BASE_URL}/games/{season_year}/{season_type}/schedule.json"
    response = requests.get(url, params={"api_key": API_KEY})
    
    if response.status_code == 200:
        print("Schedule fetched successfully!")
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def get_game_boxscore(game_id):
    url = f"{BASE_URL}/games/{game_id}/boxscore.json"
    response = requests.get(url, params={"api_key": API_KEY})
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching boxscore: {response.status_code}")
        return None

def get_player_profile(player_id):
    url = f"{BASE_URL}/players/{player_id}/profile.json"
    response = requests.get(url, params={"api_key": API_KEY})
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching player: {response.status_code}")
        return None

if __name__ == "__main__":
    print("Testing Sportradar connection...")
    schedule = get_schedule()
    
    if schedule:
        games = schedule.get("games", [])
        print(f"Found {len(games)} games in schedule")
        if games:
            print(f"First game: {games[0]}")