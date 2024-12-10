import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from datetime import datetime, timedelta
import os

def process_file(date, league, type_, range_):
    file_path = f'basketball_trends/source/proc_data/agg_raw/{league}/{date}/{type_}/{range_}_aggregated.csv'
    
    # Check if file exists to avoid FileNotFoundError
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    df = pd.read_csv(file_path)

    # Data Cleaning: Handle missing or irrelevant values
    # Convert ATS records to numeric
    def ats_to_numeric(record):
        try:
            wins, losses, ties = map(int, record.split('-'))
            return wins + 0.5 * ties - losses
        except:
            return 0  # Handle malformed data

    # Apply ats_to_numeric to all ATS record columns
    ats_columns = [col for col in df.columns if 'ATS Record' in col]
    for col in ats_columns:
        df[f'{col}_numeric'] = df[col].apply(ats_to_numeric)

    # Remove '%' symbol and convert Cover % columns to numeric
    df = df.replace({'%': '', '--': 0}, regex=True)  # Replace '--' with NaN
    cover_columns = [col for col in df.columns if 'Cover %' in col]
    df[cover_columns] = df[cover_columns].apply(pd.to_numeric, errors='coerce')

    # Fill missing values (optional: customize per project needs)
    df.fillna(0, inplace=True)  # Replace NaN with 0 to retain all rows

    # Normalize Cover %, MOV, and ATS +/- columns
    scaler = MinMaxScaler()
    normalize_columns = [col for col in df.columns if any(metric in col for metric in ['Cover %', 'MOV', 'ATS +/-'])]
    
    # Check if there are numeric values to normalize
    if normalize_columns:
        df[normalize_columns] = scaler.fit_transform(df[normalize_columns])

    # Feature Engineering
    df['Home_Away_Advantage'] = df['is_home_MOV'] - df['is_away_MOV']
    df['Rest_Days_Advantage'] = df['rest_advantage_MOV'] - df['rest_disadvantage_MOV']

    momentum_columns = [col for col in df.columns if 'all_games_ATS Record_numeric' in col]
    for col in momentum_columns:
        df[f'Momentum_{col}_Last5'] = df[col].rolling(5, min_periods=1).mean()

    df['Matchup_Strength_Diff'] = df['is_fav_MOV'] - df['is_dog_MOV']

    # Save processed data
    output_path = f'basketball_trends/source/proc_data/processed/{league}/{date}/{type_}/{range_}_processed.csv'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    # print(f"Data preprocessing and feature engineering completed for {file_path}.")

allowed_leagues = ['NBA', 'NCB']
allowed_types = ['ats']
allowed_ranges = ['yearly_since_2014_2015', 'yearly_all', 'yearly_2024_2025']  # Replace with actual allowed range values

for x in range(0, 29):
    date = (datetime.today() - timedelta(days=x)).date()

    for league in allowed_leagues:
        for type_ in allowed_types:
            for range_ in allowed_ranges:
                process_file(date, league, type_, range_)
print(f'pre_process ran')
