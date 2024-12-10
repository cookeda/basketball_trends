import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import date, timedelta
import json
import os

# Define constants
SCORES_URLS = {
    'nba': 'https://www.espn.com/nba/scoreboard/_/date/{date}',
    'ncb': 'https://www.espn.com/mens-college-basketball/scoreboard/_/date/{date}'
}

DICT_PATH = 'teams.json'
OUTPUT_FOLDER = '../raw_data'
OUTPUT_CSV = 'yesterday_scores.csv'

# Load or initialize team dictionary
def load_or_initialize_team_dict():
    if os.path.exists(DICT_PATH):
        with open(DICT_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_team_dict(team_dict):
    with open(DICT_PATH, 'w') as f:
        json.dump(team_dict, f, indent=4)

def standardize_team_name(team_name, source, team_dict):
    """Standardizes a team name based on the source and team dictionary."""
    for standard_name, mappings in team_dict.items():
        if source in mappings and team_name in mappings[source]:
            return standard_name
    # If team is new, add it to the dictionary
    if team_name not in team_dict:
        team_dict[team_name] = {source: [team_name]}
    else:
        team_dict[team_name].setdefault(source, []).append(team_name)
    return team_name

def fetch_scores(league, date_str, source, team_dict):
    """Fetch scores for the given league and date from a specific source."""
    url = SCORES_URLS[league].format(date=date_str)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    games = []

    # Extract game scores
    for game in soup.find_all('div', class_='ScoreCell__Game'):
        teams = game.find_all('span', class_='ScoreCell__TeamName')
        scores = game.find_all('div', class_='ScoreCell__Score')
        if not teams or not scores:
            continue
        
        team1 = standardize_team_name(teams[0].text.strip(), source, team_dict)
        team2 = standardize_team_name(teams[1].text.strip(), source, team_dict)
        score1 = scores[0].text.strip()
        score2 = scores[1].text.strip()

        games.append({
            'league': league.upper(),
            'team1': team1,
            'team2': team2,
            'score1': score1,
            'score2': score2
        })
    
    return games

def main():
    # Determine yesterday's date
    yesterday = date.today() - timedelta(days=1)
    date_str = yesterday.strftime('%Y%m%d')

    # Load or initialize team dictionary
    team_dict = load_or_initialize_team_dict()

    all_games = []

    # Fetch scores for both leagues
    for league in ['nba', 'ncb']:
        games = fetch_scores(league, date_str, 'espn', team_dict)
        all_games.extend(games)

    # Save updated team dictionary
    save_team_dict(team_dict)

    # Save scores to league-specific CSVs
    for league in ['NBA', 'NCB']:
        league_games = [game for game in all_games if game['league'] == league]
        if league_games:
            output_path = os.path.join(OUTPUT_FOLDER, league, yesterday.strftime('%Y-%m-%d'), OUTPUT_CSV)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            df = pd.DataFrame(league_games)
            df.to_csv(output_path, index=False)
            print(f"Scores for {league} saved to {output_path}")

if __name__ == '__main__':
    main()
