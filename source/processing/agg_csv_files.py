import pandas as pd
import glob
import os
from datetime import datetime, timedelta

def agg_files(date, league, type, range):
    # Validate inputs
    allowed_leagues = ['NBA', 'NCB']
    allowed_types = ['ou', 'ats']
    allowed_ranges = ['yearly_since_2014_2015', 'yearly_all', 'yearly_2024_2025']  # Replace with actual allowed range values

    if league not in allowed_leagues:
        raise ValueError(f"Invalid league: {league}. Allowed values are {allowed_leagues}.")
    if type not in allowed_types:
        raise ValueError(f"Invalid type: {type}. Allowed values are {allowed_types}.")
    if range not in allowed_ranges:
        raise ValueError(f"Invalid range: {range}. Allowed values are {allowed_ranges}.")

    # Define the path to the folder containing the CSV files
    path = f"basketball_trends/source/raw_data/{league}/{date}/{type}/{range}"
    filenames = glob.glob(path + "/*.csv")

    # Initialize an empty list to store DataFrames
    dfs = []

    # Loop through the filenames and process each file
    for filename in filenames:
        # Extract the base file name (to use as a new column prefix)
        base_name = os.path.basename(filename).replace('.csv', '')
        
        # Read the CSV file into a DataFrame
        df = pd.read_csv(filename)
        
        # Add a multi-level column index (team as the row index, stats with file name as prefix)
        df = df.set_index('Team').add_prefix(base_name + '_')
        
        # Append to the list of DataFrames
        dfs.append(df)

    # Merge all DataFrames horizontally by index (Team)
    big_frame = pd.concat(dfs, axis=1)

    # Define the output path
    output_path = f'basketball_trends/source/proc_data/agg_raw/{league}/{date}/{type}'
    os.makedirs(output_path, exist_ok=True)

    # Save the DataFrame to a CSV file
    big_frame.to_csv(os.path.join(output_path, f'{range}_aggregated.csv'))
    # print(f'Agg csv saved to {output_path}')


def main():
    allowed_leagues = ['NBA', 'NCB']
    allowed_types = ['ou', 'ats']
    allowed_ranges = ['yearly_since_2014_2015', 'yearly_all', 'yearly_2024_2025']  # Replace with actual allowed range values
    for x in range(0, 29):
        date = (datetime.today() - timedelta(days=x)).date()

        for league in allowed_leagues:
            for type_ in allowed_types:
                for range_ in allowed_ranges:
                    try:
                        agg_files(date, league, type_, range_)
                    except:
                        print('agg_csvs_error', date)
    print(f'agg_csv_ran')


if __name__ == '__main__':
    main()