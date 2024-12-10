import pandas as pd
from datetime import datetime, timedelta

# Define the start and end dates
start_date = datetime.strptime('2024-11-11', '%Y-%m-%d')
end_date = datetime.strptime('2024-12-09', '%Y-%m-%d')

# Initialize an empty list to collect DataFrames

current_date = start_date
unique_teams = set()  # Use a set to store unique teams

while current_date <= end_date:
    date_str = current_date.strftime('%Y-%m-%d')
    current_date += timedelta(days=1)
    try:
        file_path = f'C:/Users/dcooke/Projects/Sports/basketball_trends/source/raw_data/NCB/{date_str}/game_results.csv'
        df = pd.read_csv(file_path)
        # Add unique away and home teams to the set
        unique_teams.update(df['Away Team'].unique())
        unique_teams.update(df['Home Team'].unique())
    except FileNotFoundError:
        print(f'Missing data for {date_str}')
    except Exception as e:
        print(f"Error processing {date_str}: {e}")

# Convert the set to a sorted list (optional)
unique_teams_list = sorted(unique_teams)

from rapidfuzz import process, fuzz
import json
print(unique_teams_list)

# # Load JSON data (replace with actual file path)
# json_file_path = 'C:/Users/dcooke/Projects/Sports/basketball_trends/source/Dictionary/template/NCB.json'
# with open(json_file_path, 'r') as file:
#     json_data = json.load(file)

# # Extract team names from JSON
# team_names = [team['DraftKings Name'] for team in json_data if team['DraftKings Name']]

# name_list = unique_teams_list

# # Function to map names with fuzzy matching
# def map_names_to_teams(names, teams, threshold=80):
#     mapping = {}
#     for name in names:
#         result = process.extractOne(name, teams, scorer=fuzz.ratio)
#         if result:  # Ensure result is not None
#             match, score = result[:2]  # Unpack only the first two values
#             if score >= threshold:
#                 mapping[name] = match
#             else:
#                 mapping[name] = None  # No reliable match found
#         else:
#             mapping[name] = None  # No match found
#     return mapping

# # Map names
# name_mapping = map_names_to_teams(name_list, team_names)

# # Update JSON data with the mapping
# no_match_found = []
# for name, match in name_mapping.items():
#     if match:
#         # Find the team in the JSON data and update the Covers value
#         for team in json_data:
#             if team['DraftKings Name'] == match:
#                 team['Covers'] = name
#                 break
#     else:
#         no_match_found.append(name)

# # Save the updated JSON data back to file
# with open(json_file_path, 'w') as file:
#     json.dump(json_data, file, indent=4)

# # Print results
# print(f"Number of 'No Match Found': {len(no_match_found)}")
# print("Teams needing manual mapping:")
# print("\n".join(no_match_found))