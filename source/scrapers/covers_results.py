import csv
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from datetime import date, timedelta

def setup_driver():
    """Sets up and returns a basic Selenium WebDriver instance."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('log-level=3')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def fetch_articles_and_save_to_csv(url, output_csv):
    """Fetches titles and dynamic text from each article and saves parsed data to a CSV."""
    driver = setup_driver()
    try:
        driver.get(url)
        
        # Locate all articles dynamically
        articles = driver.find_elements(By.XPATH, "/html/body/main/div[3]/article")
        article_count = len(articles)
        if article_count > 4:
            article_count = article_count - 1
        print(f"Found {article_count} articles:")
        
        with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Away Team", "Home Team", "Cover Team", "Closing Spread", "Closing Total Line", "Actual Total Score"])
            
            for idx, article in enumerate(articles, start=1):
                try:
                    # Extract the title to determine away and home teams
                    title = article.text.split('\n')[0]  # Assuming the first line is the title
                    away_team, home_team = title.split(' @ ')
                    # print(title, away_team, home_team)

                    dynamic_text = article.find_element(By.XPATH, './div[3]').text
                    cover_team = dynamic_text.split(' covered')[0].strip()
                    spread_line = dynamic_text.split('spread of ')[1].split('. The total')[0]
                    actual_total = dynamic_text.split('The total score of ')[1].split(' was')[0]
                    total_line = dynamic_text.strip().split()[-1]
                    away_score = driver.find_elements(By.XPATH, '//*[@id="nba-315608"]/div[2]/table/tbody/tr[1]/td[5]')

                    print(f'Cover Team: {cover_team}; Spread Line: {spread_line}; Actual Total: {actual_total}; Total Line: {total_line} ')

                    # Write extracted data to CSV
                    writer.writerow([away_team, home_team, cover_team, spread_line, total_line, actual_total, away_score])

                except NoSuchElementException:
                    print(f"Dynamic text not found for Article {idx}")
                except ValueError:
                    print()
                except Exception as e:
                    print(f"Error processing Article {idx}: {e}")
    finally:
        driver.quit()

def main():
    # Main Execution
    league_list = ['NCB', 'NBA']
    for league in league_list:
        selected_date = date.today() - timedelta(days = 1)
        if league == 'NCB': selected_league = 'ncaab'
        else: selected_league = league
        url = f"https://www.covers.com/sports/{selected_league}/matchups?selectedDate={selected_date}"
        output_csv = f"../raw_data/{league}/{selected_date}/game_results.csv"
        fetch_articles_and_save_to_csv(url, output_csv)


if __name__ == '__main__':
    main()