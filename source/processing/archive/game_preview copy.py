import pandas as pd
import os
from datetime import datetime, timedelta
import json

# Configure pandas to display all rows and columns
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.colheader_justify', 'left')

def grab_spread_line(league, date, team_name):
    with open(f'basketball_trends/source/raw_data/{league}/{date}/dk_odds.json', 'r', encoding='utf-8') as f:
       json_data = json.load(f)
    for game in json_data:
        game_info = game[0]  # Extract the game dictionary
        if game_info["Away Team"] == team_name:
            if game_info['Away Spread'][0] == '+':
                   underdog = True
            else: underdog = False
            return {
                "Team": team_name,
                "Spread": game_info["Away Spread"],
                "Odds": game_info["Away Spread Odds"],
                "Underdog": underdog
            }
        if game_info["Home Team"] == team_name:
            if game_info['Home Spread'][0] == '+':
                   underdog = True
            else: underdog = False
            return {
                "Team": team_name,
                "Spread": game_info["Home Spread"],
                "Odds": game_info["Home Spread Odds"],
                "Underdog": underdog

            }
    return {"error": f"Team '{team_name}' not found in the data."}


def grab_name_info(df, league):
    if league == 'NBA':
        path = 'basketball_trends/source/Dictionary/Pro/NBA.json'
    elif league == 'NCB':
        path = 'basketball_trends/source/Dictionary/College/NCB.json'
    with open(path, 'r') as f:
        team_mappings = json.load(f)
    team_mappings_df = pd.DataFrame(team_mappings)

    # Debugging: Print structure of team mappings
#     print("Team mappings DataFrame structure:")
#     print(team_mappings_df.head())

    # Normalize only for lookup, without modifying the original data
    team_mappings_df['Team Rankings Name (Lower)'] = team_mappings_df['Team Rankings Name'].str.strip().str.lower()

    # Temporary lowercase columns for lookup
    df['Away Team (Lower)'] = df['Away Team'].str.strip().str.lower()
    df['Home Team (Lower)'] = df['Home Team'].str.strip().str.lower()

    # Merge DraftKings Name for Away Team
    df = df.merge(
        team_mappings_df[['Team Rankings Name (Lower)', 'DraftKings Name']],
        left_on='Away Team (Lower)',
        right_on='Team Rankings Name (Lower)',
        how='left'
    ).rename(columns={'DraftKings Name': 'Away Team DraftKings'}).drop(columns=['Team Rankings Name (Lower)', 'Away Team (Lower)'])

    # Merge DraftKings Name for Home Team
    df = df.merge(
        team_mappings_df[['Team Rankings Name (Lower)', 'DraftKings Name']],
        left_on='Home Team (Lower)',
        right_on='Team Rankings Name (Lower)',
        how='left'
    ).rename(columns={'DraftKings Name': 'Home Team DraftKings'}).drop(columns=['Team Rankings Name (Lower)', 'Home Team (Lower)'])

    # Debugging: Verify structure after merging DraftKings names
#     print("After merging DraftKings names:")
#     print(df.head())
    return df

def generate_preview(league, date):
    df = pd.read_csv(f'basketball_trends/source/raw_data/{league}/{date}/daily_schedule.csv')

    # Debugging: Check initial structure of daily schedule
    # print("Daily schedule DataFrame structure:")
    # print(df.head())

    away_pattern = r"(?:#(\d+)\s+)?([^#]+)\s+(?:at|vs.)"
    home_pattern = r"(?:at|vs.)\s+(?:#(\d+)\s+)?(.+)$"

    # Extract and strip team names
    df[['Away Team Rank', 'Away Team']] = df['Matchup'].str.extract(away_pattern)
    df[['Home Team Rank', 'Home Team']] = df['Matchup'].str.extract(home_pattern)
    df['Away Team'] = df['Away Team'].str.strip().str.title()
    df['Home Team'] = df['Home Team'].str.strip().str.title()
    df['Away Team Rank'] = pd.to_numeric(df['Away Team Rank'], errors='coerce').fillna(0).astype(int)
    df['Home Team Rank'] = pd.to_numeric(df['Home Team Rank'], errors='coerce').fillna(0).astype(int)
    df = df.drop(columns=['Matchup'])

    # Add DraftKings info
    df = grab_name_info(df, league)

    # Add Spread Line and Underdog/Favorite Info
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

    # Convert the spread data to a DataFrame and merge it with the main DataFrame
    spread_df = pd.DataFrame(spread_data)
    df = pd.concat([df, spread_df], axis=1)

    # Debugging: Verify spread data addition
    # print("Preview DataFrame with Spread Data:")
    print(df.head())

    # Process aggregate data
    agg_curr = pd.read_csv(f'basketball_trends/source/proc_data/agg_raw/{league}/{date}/ats/yearly_2024_2025_aggregated.csv')

    filtered_agg = agg_curr[['Team', 'all_games_ATS Record', 'all_games_Cover %', 'all_games_MOV',
                             'all_games_ATS +/-', 'is_away_ATS Record', 'is_away_Cover %',
                             'is_away_MOV', 'is_away_ATS +/-', 'is_home_ATS Record', 'is_home_Cover %',
                             'is_home_MOV', 'is_home_ATS +/-', 'is_dog_ATS Record', 'is_dog_Cover %',
                             'is_dog_MOV', 'is_dog_ATS +/-', 'is_fav_ATS Record', 'is_fav_Cover %',
                             'is_fav_MOV', 'is_fav_ATS +/-']].copy()

    filtered_agg['Team'] = filtered_agg['Team'].str.strip().str.title()

    # Perform the merge
    df = df.merge(filtered_agg.add_prefix('Away Team '), 
                  left_on='Away Team', 
                  right_on='Away Team Team', 
                  how='left')


    # Save to a CSV for preview
    df.to_csv('preview.csv', index=False)

    return df

       #TODO: Underdog/Favorite (Line Data), Append cover team in results copy
       
def main():
       league_list = ['NBA', 'NCB']
       today = datetime.now()
       start_date = datetime(2024, 11, 10)

       # Generate a list of dates from start_date to today
       date_list = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') 
              for i in range((today - start_date).days + 1)]

       # Output the generated list
       # for date in date_list:
       #        for league in league_list:
       #               generate_preview(league, date)
       generate_preview('NBA', '2024-11-20')
       print(grab_spread_line('NBA', '2024-11-20', 'CHI Bulls'))
       print(grab_spread_line('NBA', '2024-11-20', 'MIL Bucks'))

if __name__ == '__main__':
       main()