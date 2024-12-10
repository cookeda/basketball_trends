import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import date
import os
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from selenium.common.exceptions import WebDriverException
from fake_useragent import UserAgent

def main():
    # Set up Selenium with headless Chrome and proxy rotation
    def setup_driver(proxy=None):
        """Sets up and returns a new Selenium WebDriver instance with user-agent and proxy rotation."""
        ua = UserAgent()
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('log-level=3')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("--disable-extensions")
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument(f'user-agent={ua.random}')
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    errors = []  # Collect errors for reporting

    def scrape_table(driver, url, league, date_to_scrape, condition, range_folder, key, table_id="DataTables_Table_0"):
        """Scrapes a table from the given URL and saves it as a CSV file."""
        base_path = f"../raw_data/{league.upper()}/{date_to_scrape}/{key}/{range_folder}/"
        os.makedirs(base_path, exist_ok=True)
        file_name = os.path.join(base_path, f"{condition}.csv")

        if Path(file_name).exists():
            return  # Skip if file already exists

        try:
            # print(url)
            driver.get(url)
            time.sleep(random.uniform(3, 7))  # Random delay between requests
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"#{table_id}"))
            )
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table = soup.find("table", {"id": table_id})
            if not table:
                raise ValueError(f"No table found at {url}")

            headers = [header.text.strip() for header in table.find_all("th")]
            data = [[cell.text.strip() for cell in row.find_all("td")] for row in table.find("tbody").find_all("tr")]
            df = pd.DataFrame(data, columns=headers)
            df.to_csv(file_name, index=False)
        except Exception as e:
            errors.append(f"Error scraping {url}: {e}")

    def scrape_table_with_retry(driver, url, league, date_to_scrape, condition, range_folder, key, retries=3):
        """Retries scraping a table for a given number of attempts."""
        for attempt in range(retries):
            try:
                scrape_table(driver, url, league, date_to_scrape, condition, range_folder, key)
                break
            except WebDriverException as e:
                if attempt < retries - 1:
                    time.sleep(random.uniform(5, 10))  # Wait before retrying
                    continue
                else:
                    errors.append(f"Failed after {retries} retries: {url} | Error: {e}")

    def scrape_trends_table(driver, league, date_to_scrape, trend_type, pbar):
        """Scrapes trends for a given league and trend type (ats, ou)."""
        key_list = [
            "all_games", "is_after_win", "is_after_loss", 
            "is_home", "is_away", "is_fav", 
            "is_dog", "rest_advantage", "rest_disadvantage", 
            "equal_rest", "four_plus_days_off", "two_three_days_off", 
            "one_day_off", "no_rest"
        ]
        range_list = ["yearly_all", "yearly_2024_2025", "yearly_since_2014_2015"]

        for key in key_list:
            for range_folder in range_list:
                url = f"https://www.teamrankings.com/{league}/trends/{trend_type}_trends/?sc={key}&range={range_folder}"
                #https://www.teamrankings.com/nba/trends/ats_trends/?sc=is_home&range=yearly_all
                pbar.set_description(f"{league.upper()}: {trend_type}, {range_folder}, {key}")
                scrape_table_with_retry(driver, url, league, date_to_scrape.strftime("%Y-%m-%d"), key, range_folder, trend_type)
                pbar.update(1)

    def scrape_trends(driver, league, date_to_scrape, pbar):
        trend_types = ["ou", "ats"]
        for trend_type in trend_types:
            scrape_trends_table(driver, league, date_to_scrape, trend_type, pbar)

    def scrape_sched_day(driver, league, date_to_scrape):
        """Fetches daily schedule and saves it in the same hierarchy."""
        full_url = f"https://www.teamrankings.com/{league}/schedules/?date={date_to_scrape}"
        base_path = f"../raw_data/{league.upper()}/{date_to_scrape}/"
        os.makedirs(base_path, exist_ok=True)
        file_name = os.path.join(base_path, "daily_schedule.csv")

        if Path(file_name).exists():
            return  # Skip if file already exists

        try:
            # print(full_url)
            driver.get(full_url)
            time.sleep(random.uniform(3, 9))  # Random delay
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#DataTables_Table_0"))
            )
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table = soup.find("table", {"id": "DataTables_Table_0"})
            headers = [header.text.strip() for header in table.find_all("th")]
            data = [[cell.text.strip() for cell in row.find_all("td")] for row in table.find("tbody").find_all("tr")]
            df = pd.DataFrame(data, columns=headers)
            df.to_csv(file_name, index=False)
        except Exception as e:
            errors.append(f"Error scraping daily schedule for {league}: {e}")

    def process_league(league, date_to_scrape):
        """Processes a single league by scraping schedule and trends."""
        driver = setup_driver()
        try:
            with tqdm(total=total_league_tasks, desc=f"{league.upper()} Progress", leave=True) as pbar:
                scrape_sched_day(driver, league, date_to_scrape)
                scrape_trends(driver, league, date_to_scrape, pbar)
        finally:
            driver.quit()

    # Main Execution
    today_date = date.today()
    league_list = ['nba', 'ncb']

    total_league_tasks = len(["ou", "ats"]) * len([
        "all_games", "is_after_win", "is_after_loss", "is_home", "is_away", "is_fav", "is_dog", 
        "rest_advantage", "rest_disadvantage", "equal_rest", "four_plus_days_off", 
        "two_three_days_off", "one_day_off", "no_rest"
    ]) * len(["yearly_all", "current", "yearly_since_2014_2015"])

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(process_league, league, today_date) for league in league_list]
        for future in futures:
            future.result()

    # Display errors at the end
    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(error)


if __name__ == '__main__':
    try:
        main()
    except:
        main()