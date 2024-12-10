import pandas as pd
from datetime import date


def clean_schedule(league):
    todays_date = date.today()
    df = pd.read_csv(f'basketball_trends/source/raw_data/{league}/{todays_date}/daily_schedule.csv')
    print(df)

    clean_df = pd.DataFrame()
    for x in range(len(df)):
        try:
            try:
                matchup_string = (df['Matchup'][x].split(' at '))
            except:
                matchup_string = (df['Matchup'][x].split(' vs. '))

#            print(matchup_string)

            away_team = matchup_string[0] 
            home_team = matchup_string[1]

            away_team = away_team.strip()
            home_team = home_team.strip()


            print(f"'{away_team}' at '{home_team}'")
            clean_df[x][away_team] = away_team
            clean_df[x][home_team] = home_team
        except Exception as error:
            print(f"Error on Index: {x} {error}. {df['Matchup'][x]}")


    return clean_df

def aggregate_all_csv(league):
    todays_date = date.today()

    df = pd.read_csv(f'basketball_trends/source/raw_data/{league}/{todays_date}/ats/current/all_games.csv')
    return df




print(clean_schedule('NCB'))
print(aggregate_all_csv('NBA'))