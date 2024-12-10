import pandas as pd
import os
from datetime import datetime, timedelta
import json
import numpy as np

# Configure pandas display options for better debugging and visualization
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.colheader_justify', 'left')


def load_json(file_path):
    """Load a JSON file and return its content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Failed to decode JSON from: {file_path}")


def grab_spread_line(league, date, team_name):
    """Retrieve spread line and related data for a team."""
    file_path = f'basketball_trends/source/raw_data/{league}/{date}/dk_odds.json'
    json_data = load_json(file_path)

    for game in json_data:
        game_info = game[0]  # Extract the game dictionary
        if game_info["Away Team"] == team_name:
            underdog = game_info['Away Spread'][0] == '+'
            return {
                "Team": team_name,
                "Spread": game_info["Away Spread"],
                "Odds": game_info["Away Spread Odds"],
                "Underdog": underdog
            }
        elif game_info["Home Team"] == team_name:
            underdog = game_info['Home Spread'][0] == '+'
            return {
                "Team": team_name,
                "Spread": game_info["Home Spread"],
                "Odds": game_info["Home Spread Odds"],
                "Underdog": underdog
            }

    return {"error": f"Team '{team_name}' not found in the data."}


def load_team_mappings(league):
    """Load team mappings for a specific league."""
    if league == 'NBA':
        path = 'basketball_trends/source/Dictionary/Pro/NBA.json'
    elif league == 'NCB':
        path = 'basketball_trends/source/Dictionary/College/NCB.json'
    else:
        raise ValueError(f"Unsupported league: {league}")

    return load_json(path)

def add_underdog_favorite_stats(df):
    """
    Create columns for underdog stats and favorite stats based on whether a team is favored or not.

    Parameters:
    df (pd.DataFrame): The DataFrame to process.

    Returns:
    pd.DataFrame: The DataFrame with new underdog and favorite stats columns.
    """
    underdog_stats = []
    favorite_stats = []

    for _, row in df.iterrows():
        # Determine if away or home team is the underdog
        if row['Away Team Underdog']:
            underdog_stats.append({
                'Team': row['Away Team'],
                'Spread': row['Away Team Spread'],
                'Odds': row['Away Team Odds'],
                'ATS Record': row['Away Team is_dog_ATS Record'],
                'Cover %': row['Away Team is_dog_Cover %'],
                'MOV': row['Away Team is_dog_MOV'],
                'ATS +/-': row['Away Team is_dog_ATS +/-']
            })
            favorite_stats.append({
                'Team': row['Home Team'],
                'Spread': row['Home Team Spread'],
                'Odds': row['Home Team Odds'],
                'ATS Record': row['Home Team is_fav_ATS Record'],
                'Cover %': row['Home Team is_fav_Cover %'],
                'MOV': row['Home Team is_fav_MOV'],
                'ATS +/-': row['Home Team is_fav_ATS +/-']
            })
        else:
            underdog_stats.append({
                'Team': row['Home Team'],
                'Spread': row['Home Team Spread'],
                'Odds': row['Home Team Odds'],
                'ATS Record': row['Home Team is_dog_ATS Record'],
                'Cover %': row['Home Team is_dog_Cover %'],
                'MOV': row['Home Team is_dog_MOV'],
                'ATS +/-': row['Home Team is_dog_ATS +/-']
            })
            favorite_stats.append({
                'Team': row['Away Team'],
                'Spread': row['Away Team Spread'],
                'Odds': row['Away Team Odds'],
                'ATS Record': row['Away Team is_fav_ATS Record'],
                'Cover %': row['Away Team is_fav_Cover %'],
                'MOV': row['Away Team is_fav_MOV'],
                'ATS +/-': row['Away Team is_fav_ATS +/-']
            })

    underdog_df = pd.DataFrame(underdog_stats).add_prefix('Underdog is_dog ')
    favorite_df = pd.DataFrame(favorite_stats).add_prefix('Favorite is_fav ')

    # Concatenate new columns to the existing DataFrame
    df = pd.concat([df, underdog_df, favorite_df], axis=1)

    return df

def grab_name_info(df, league):
    """Map team names from Team Rankings to DraftKings names."""
    team_mappings = load_team_mappings(league)
    team_mappings_df = pd.DataFrame(team_mappings)

    # Normalize team names for matching
    team_mappings_df['Team Rankings Name (Lower)'] = team_mappings_df['Team Rankings Name'].str.strip().str.lower()
    df['Away Team (Lower)'] = df['Away Team'].str.strip().str.lower()
    df['Home Team (Lower)'] = df['Home Team'].str.strip().str.lower()

    # Merge DraftKings names for Away and Home teams
    df = df.merge(
        team_mappings_df[['Team Rankings Name (Lower)', 'DraftKings Name', 'Covers']],
        left_on='Away Team (Lower)',
        right_on='Team Rankings Name (Lower)',
        how='left'
    ).rename(columns={
        'DraftKings Name': 'Away Team DraftKings',
        'Covers': 'Away Team Covers'
    }).drop(columns=['Team Rankings Name (Lower)', 'Away Team (Lower)'])

    df = df.merge(
        team_mappings_df[['Team Rankings Name (Lower)', 'DraftKings Name', 'Covers']],
        left_on='Home Team (Lower)',
        right_on='Team Rankings Name (Lower)',
        how='left'
    ).rename(columns={
        'DraftKings Name': 'Home Team DraftKings',
        'Covers': 'Home Team Covers'
    }).drop(columns=['Team Rankings Name (Lower)', 'Home Team (Lower)'])
    
    return df


def drop_irrelevant_stats(df):
    """
    Drop columns related to 'Away Team is_home' and 'Home Team is_away' stats.

    Parameters:
    df (pd.DataFrame): The DataFrame to process.

    Returns:
    pd.DataFrame: The DataFrame with irrelevant columns dropped.
    """
    df = add_underdog_favorite_stats(df)

    columns_to_drop = [
        col for col in df.columns 
        if col.startswith('Away Team is_home') or col.startswith('Home Team is_away') or
           col.startswith('Away Team is_after') or col.startswith('Home Team is_after') or
           ('rest') in col.lower() or ('days') in col.lower() or ('day') in col.lower() or
           col.startswith('Away Team is_fav') or col.startswith('Away Team is_dog') or
           col.startswith('Home Team is_fav') or col.startswith('Home Team is_dog')
    ]
    df = df.drop(columns=columns_to_drop, errors='ignore')

    # Print debug information about dropped columns
    # print(f"Dropped columns: {columns_to_drop}")
    
    
    return df


def process_schedule_data(league, date):
    """Load and process the daily schedule data."""
    file_path = f'basketball_trends/source/raw_data/{league}/{date}/daily_schedule.csv'
    df = pd.read_csv(file_path)

    # Extract and clean team names from Matchup column
    away_pattern = r"(?:#(\d+)\s+)?([^#]+)\s+(?:at|vs.)"
    home_pattern = r"(?:at|vs.)\s+(?:#(\d+)\s+)?(.+)$"

    df[['Away Team Rank', 'Away Team']] = df['Matchup'].str.extract(away_pattern)
    df[['Home Team Rank', 'Home Team']] = df['Matchup'].str.extract(home_pattern)

    df['Away Team'] = df['Away Team'].str.strip().str.title()
    df['Home Team'] = df['Home Team'].str.strip().str.title()
    df['Away Team Rank'] = pd.to_numeric(df['Away Team Rank'], errors='coerce').fillna(0).astype(int)
    df['Home Team Rank'] = pd.to_numeric(df['Home Team Rank'], errors='coerce').fillna(0).astype(int)
    df = df.drop(columns=['Matchup'])

    return grab_name_info(df, league)


def add_spread_data(df, league, date):
    """Add spread data to the schedule DataFrame."""
    spread_data = []
    for _, row in df.iterrows():
        away_data = grab_spread_line(league, date, row['Away Team DraftKings'])
        home_data = grab_spread_line(league, date, row['Home Team DraftKings'])

        spread_data.append({
            "Away Team Spread": away_data.get("Spread", "N/A"),
            "Away Team Odds": away_data.get("Odds", "N/A"),
            "Away Team Underdog": away_data.get("Underdog", False),
            "Home Team Spread": home_data.get("Spread", "N/A"),
            "Home Team Odds": home_data.get("Odds", "N/A"),
            "Home Team Underdog": home_data.get("Underdog", False)
        })

    spread_df = pd.DataFrame(spread_data)
    return pd.concat([df, spread_df], axis=1)


def generate_preview(league, date, range_):
    """Generate a preview of game data including spread lines and aggregate stats."""
    schedule_df = process_schedule_data(league, date)
    schedule_df = add_spread_data(schedule_df, league, date)

    # Load aggregate ATS data
    agg_file = f'basketball_trends/source/proc_data/agg_raw/{league}/{date}/ats/{range_}.csv'
    agg_df = pd.read_csv(agg_file)
    agg_df['Team'] = agg_df['Team'].str.strip().str.title()

    # Merge aggregate data
    schedule_df = schedule_df.merge(
        agg_df.add_prefix('Away Team '),
        left_on='Away Team',
        right_on='Away Team Team',
        how='left'
    )
    
    schedule_df = schedule_df.merge(
        agg_df.add_prefix('Home Team '),
        left_on='Home Team',
        right_on='Home Team Team',
        how='left'
    )
    # schedule_df = add_underdog_favorite_stats(schedule_df)

    schedule_df = drop_irrelevant_stats(schedule_df)


    schedule_df = schedule_df.fillna(0)

    # Save the preview to a CSV
    output_path = f'basketball_trends/source/proc_data/preview/{league}/{date}/ats/'
    os.makedirs(output_path, exist_ok=True)
    schedule_df.to_csv(f'{output_path}{range_}.csv', index=False)
    schedule_df.to_pickle(f'{output_path}{range_}.pkl')
    # print(f"Preview saved to {output_path}")
    # print(schedule_df.columns)
    
    return schedule_df


def main():
    league_list = ['NBA', 'NCB']
    today = datetime.now()
    start_date = datetime(2024, 11, 10)

    # Generate a list of dates from start_date to today
    date_list = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') 
        for i in range((today - start_date).days + 1)]

    range_list = ['yearly_2024_2025_aggregated', 'yearly_all_aggregated', 'yearly_since_2014_2015_aggregated']

    # Output the generated list
    for date in date_list:
            for league in league_list:
                for range_ in range_list:
                    try:
                        generate_preview(league, date, f'{range_}')
                    except Exception as e:
                        print(f'Error on {league}/{date}: {e}')
    print(f'game_preview_v2 saved')
    # # Example usage of grab_spread_line
    # print(grab_spread_line(league, date, 'CHI Bulls'))
    # print(grab_spread_line(league, date, 'MIL Bucks'))


if __name__ == '__main__':
    main()
