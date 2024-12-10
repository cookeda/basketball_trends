import pandas as pd
from datetime import datetime, timedelta

# Define the start and end dates
start_date = datetime.strptime('2024-11-10', '%Y-%m-%d')
end_date = datetime.strptime('2024-12-07', '%Y-%m-%d')

# Initialize an empty list to collect DataFrames
df_list = []

# Iterate over all dates in the range
current_date = start_date
while current_date <= end_date:
    date_str = current_date.strftime('%Y-%m-%d')
    try:
        # Read the CSV for the current date
        file_path = f'C:/Users/dcooke/Projects/Sports/basketball_trends/source/proc_data/preview/NCB/{date_str}/ats/final_preprocess.csv'
        df = pd.read_csv(file_path)

        # Drop columns containing certain keywords
        columns_to_drop = [col for col in df.columns if 'Underdog' in col or 'Favorite' in col or 'Team Covers_last' in col or 'Team Covers_all' in col or 'Unnamed' in col]
        df.drop(columns=columns_to_drop, inplace=True, errors='ignore')

        # Drop specific columns
        specific_columns_to_drop = [
            'Away Team Covers_current_season', 'Away Team_current_season',
            'Home Team_current_season', 'Home Team Covers_current_season',
            'Home Team', 'Away Team', 'Time_current_season',
            'Location_current_season', 'Hotness Score_current_season',
            'Rank_current_season'
        ]
        df.drop(columns=specific_columns_to_drop, inplace=True, errors='ignore')

        # Reset the index
        df.reset_index(drop=True, inplace=True)

        # Append the processed DataFrame to the list
        df_list.append(df)

        print(f"Processed file for date: {date_str}")
    except FileNotFoundError:
        print(f"File not found for date: {date_str}, skipping...")
    except Exception as e:
        print(f"Error processing file for date: {date_str} - {e}")

    # Move to the next day
    current_date += timedelta(days=1)

# Combine all DataFrames into one
combined_df = pd.concat(df_list, ignore_index=True)

# Print the resulting DataFrame's columns
print("Combined DataFrame Columns:")
print(combined_df.columns)

# Save the combined DataFrame (optional)
combined_df.to_csv('C:/Users/dcooke/Projects/Sports/basketball_trends/source/model_v0/coll_data.csv', index=False)
