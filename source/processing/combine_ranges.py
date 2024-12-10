import pandas as pd

def main(league, date):
    df_current_season = pd.read_pickle(f'basketball_trends/source/proc_data/preview/{league}/{date}/ats/yearly_2024_2025_aggregated.pkl')
    df_all_time = pd.read_pickle(f'basketball_trends/source/proc_data/preview/{league}/{date}/ats/yearly_all_aggregated.pkl')
    df_last_10_seasons = pd.read_pickle(f'basketball_trends/source/proc_data/preview/{league}/{date}/ats/yearly_since_2014_2015_aggregated.pkl')
        
        

    # Add suffix to columns based on the time range
    df_current_season = df_current_season.add_suffix('_current_season')
    df_all_time = df_all_time.add_suffix('_all_time')
    df_last_10_seasons = df_last_10_seasons.add_suffix('_last_10_seasons')

    # Merge the DataFrames
    aggregated_df = pd.concat([df_current_season, df_all_time, df_last_10_seasons], axis=1)

    # Save the aggregated DataFrame to a new CSV file
    output_file = f"basketball_trends/source/proc_data/preview/{league}/{date}/ats/agg_preview.csv"
    aggregated_df.to_csv(output_file, index=False)
    
if __name__ == '__main__':
    from datetime import datetime, timedelta
    league_list = ['NBA', 'NCB']
    for x in range(0, 29):
        for league in league_list:
            date = (datetime.today() - timedelta(days=x)).date()
            try:
                main(league, date)
            except:
                print('Combine error', date)

    # league, date = 'NBA', '2024-12-09'
    # main(league, date)
    print('COMBINE RANGES RAN')