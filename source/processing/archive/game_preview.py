import pandas as pd
import json

league = 'NBA'
date = '2024-11-10'

df = pd.read_csv(f'basketball_trends/source/raw_data/{league}/{date}/daily_schedule.csv')
# print(df.columns)
# print(df)
away_pattern = r"(?:#(\d+)\s+)?([^#]+)\s+(?:at|vs.)"
home_pattern = r"(?:at|vs.)\s+(?:#(\d+)\s+)?(.+)$"

# Extracting Away Rank and Team
df[['Away Team Rank', 'Away Team']] = df['Matchup'].str.extract(away_pattern)

# Extracting Home Rank and Team
df[['Home Team Rank', 'Home Team']] = df['Matchup'].str.extract(home_pattern)

# Fill NaN with 0 and convert to int
df['Away Team Rank'] = pd.to_numeric(df['Away Team Rank'], errors='coerce').fillna(0).astype(int)
df['Home Team Rank'] = pd.to_numeric(df['Home Team Rank'], errors='coerce').fillna(0).astype(int)


# Drop the original 'Matchup' column if no longer needed
df = df.drop(columns=['Matchup'])
print(df)

agg_curr = pd.read_csv(f'basketball_trends/source/proc_data/agg_raw/{league}/{date}/ats/yearly_2024_2025_aggregated.csv')
# print(agg_curr.columns)

relevant_column = ['ATS Record', 'Cover %', 'MOV']
filtered_agg = agg_curr[['Team', 'all_games_ATS Record', 'all_games_Cover %', 'all_games_MOV',
       'all_games_ATS +/-', 'is_away_ATS Record', 'is_away_Cover %',
       'is_away_MOV', 'is_away_ATS +/-', 'is_dog_ATS Record', 'is_dog_Cover %',
       'is_dog_MOV', 'is_dog_ATS +/-', 'is_fav_ATS Record', 'is_fav_Cover %',
       'is_fav_MOV', 'is_fav_ATS +/-', 'is_home_ATS Record', 'is_home_Cover %',
       'is_home_MOV', 'is_home_ATS +/-']]
print(filtered_agg)