import pandas as pd
import os
from datetime import datetime, timedelta

def norm_ats(date, league, type, range):
    # Format the date as a string for the file path
    date_str = date.strftime('%Y-%m-%d')
    
    # Construct the input file path
    file_path = f'../raw_data/{league}/{date_str}/{type}/{range}/no_rest.csv'
    
    # Check if file exists before proceeding
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist. Skipping...")
        return

    # Read and process the data
    df = pd.read_csv(file_path)
    print("Columns in the file:", df.columns)

    df['Cover %'] = df['Cover %'].str.rstrip('%').astype(float)
    df['gp'] = df['ATS Record'].apply(lambda x: sum(map(int, x.split('-'))))

    columns = ['gp', 'Cover %', 'MOV', 'ATS +/-']
    for column in columns:
        df[f'norm_{column}'] = df[column].apply(lambda x: (x - df[column].min()) / (df[column].max() - df[column].min()))

    df['good_score'] = (
        df['norm_gp'] * 0.15 +
        df['norm_Cover %'] * 0.3 +
        df['norm_ATS +/-'] * 0.2 +
        df['norm_MOV'] * 0.35
    )

    result_df = df[['Team', 'gp', 'good_score']].sort_values(by='good_score', ascending=False)

    # Construct the output path
    output_path = f'../proc_data/norm/{league}/{date_str}/{type}/{range}/no_rest.csv'
    os.makedirs(output_path, exist_ok=True)

    # Save the result to a CSV file
    output_file = os.path.join(output_path, f'{range}_nr.csv')
    result_df.to_csv(output_file, index=False)
    
    print(f'Norm csv saved to {output_file}')

def norm_ou

def main():
    date = (datetime.today() - timedelta(days=2)).date()
    allowed_leagues = ['NBA', 'NCB']
    allowed_types = ['ou', 'ats']
    allowed_ranges = ['yearly_since_2014_2015', 'yearly_all', 'yearly_2024_2025']
    norm_files(date, 'NBA', 'ats', 'yearly_all')
    # for league in allowed_leagues:
    #     for type in allowed_types:
    #         for range in allowed_ranges:
    #             agg_files(date, league, type, range)

if __name__ == "__main__":
    main()
