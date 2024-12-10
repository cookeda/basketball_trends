# -*- coding: utf-8 -*-
"""
Created on Sat Nov 30 14:53:18 2024

@author: dcooke
"""

import pandas as pd
import json
import os

def append_home_cover(df, league, date):
    # Load the game_results.csv
    game_results_path = f'C:/Users/dcooke/Projects/Sports/basketball_trends/source/raw_data/{league}/{date}/game_results.csv'
    if not os.path.exists(game_results_path):
        print(f"game_results.csv not found for date {date}. Skipping.")
        return df  # Return the original DataFrame if the file doesn't exist

    game_results = pd.read_csv(game_results_path)

    # Merge game_results.csv with the final DataFrame
    df = pd.merge(
        df,
        game_results[['Away Team', 'Home Team', 'Home Cover']],
        left_on=['Away Team Covers_current_season', 'Home Team Covers_current_season'],
        right_on=['Away Team', 'Home Team'],
        how='left'
    )
    return df

pd.set_option('display.max_rows', None)  # Show all rows
pd.set_option('display.max_columns', None)  # Show all columns
def main(league, date):
    df = pd.read_csv(f'C:/Users/dcooke/Projects/Sports/basketball_trends/source/proc_data/preview/{league}/{date}/ats/agg_preview.csv')
    # print(df.columns)
    range_list = ['_last_10_seasons', '_all_time']
    col_list = ['Rank', 'Hotness Score', 'Time', 'Location', 'Home Team Team', 
                'Away Team Team', 'Home Team Rank', 'Away Team Rank', 
                'Away Team DraftKings', 'Home Team DraftKings', 
                'Home Team Underdog', 'Away Team Underdog',
                'Underdog is_dog Team', 'Favorite is_fav Team', 'Away Team', 
                'Home Team', 'Underdog is_dog Odds', 'Favorite is_fav Odds', 
                'Away Team Odds', 'Home Team Odds']
    for r in range_list:
        for col in col_list:
            # print(f'Dropping "{col}{r}"')
            df = df.drop(columns = f'{col}{r}')
            
    col_list2 = ['Away Team DraftKings_current_season', 'Home Team DraftKings_current_season', 'Away Team Team_current_season', 'Home Team Team_current_season']

    for col in col_list2:
        df = df.drop(columns=col)
            
    for column in df.columns:
        if "Cover %" in column:
            df[column] = round(df[column].str.rstrip('%').astype(float) / 100, 4)

    for column in df.columns:
        if "ATS Record" in column:
            # Split the W-L-T into separate components
            try:
                record_split = df[column].str.split('-', expand=True).astype(int)
                df[column] = record_split[0] + record_split[1] + record_split[2]
            except:
                df[column] = 0
            #df[f'{column}_WinRate'] = record_split[0] / df[f'{column}_TotalGames']
            df.rename(columns={column: column.replace("ATS Record", "Sample Size")}, inplace=True)

    if league == 'NBA':
        sub_key = 'Pro'
    else:
        sub_key = 'College'
    with open(f'C:\\Users\\dcooke\\Projects\\Sports\\basketball_trends\\source\\Dictionary\\{sub_key}\\{league}_mapping.json', 'r') as f:
        data = json.load(f)

    team_col_list = ['Away Team_current_season', 'Home Team_current_season', 'Favorite is_fav Team_current_season', 'Underdog is_dog Team_current_season']
    #Encode team names
    for col in team_col_list:
        # print(df[col][1])
        # team_name = df[col].split[' ']
        # team = f'{team_name[0].upper()} {team_name[1]}'
        df[f'{col}_map'] = df[col].map(data['Team Encoding Mapping'])
        # new_col = col.replace('_current_season', '')
        # df.rename(columns={col: new_col}, inplace=True)
        # with open('C:\\Users\\dcooke\\Projects\\Sports\\basketball_trends\\source\\Dictionary\\Pro\\NBA_mapping.json', 'r') as f:
        #     data = json.load(f)

        # for _, row in df.iterrows():
        #     print(row[col], data['Team Encoding Mapping'][row[col]])
            
        #     # df[col] = data['Team Encoding Mapping'][row[col]]
        # # print(data['Team Encoding Mapping'][df[col][1]])

    def convert_american_odds_to_probability(odds):
        # Check if the odds are negative (indicating a favorite)
        fav = odds[0] == '-'
        odds = int(odds[1:])
        
        if not fav:
            return odds / (odds + 100)
        else:
            return 100 / (odds + 100)

    # Iterate through all columns containing "Odds"
    for column in df.columns:
        if "Odds" in column:
            df = df.dropna()
            # Convert each value in the column from American odds to implied probability
            df[column] = round(df[column].apply(convert_american_odds_to_probability), 4)
            df.rename(columns={column:column.replace("Odds", "Implied Odds")}, inplace=True)

    df = append_home_cover(df, league, date)
    
    


    # print(df.columns)
    folder_path = f'C:/Users/dcooke/Projects/Sports/basketball_trends/source/proc_data/preview/{league}/{date}/ats/'
    os.makedirs(folder_path, exist_ok=True)
    df.to_csv(f'{folder_path}final_preprocess.csv')

if __name__ == '__main__':
    from datetime import datetime, timedelta
    league_list = ['NCB']
    for league in league_list:
        for x in range(1, 29):
            date = (datetime.today() - timedelta(days=x)).date()
            # try:
            print(date)
            main(league, date)
            # except Exception as e:
                # print('Final error', date, league, e)
    # main('NBA', '2024-12-06')

    print('final_preprocess ran')