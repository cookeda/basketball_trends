from selenium import webdriver
webdriver.Chrome
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import json
import time
import os

options = Options()
#options.add_argument('--headless')
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument('log-level=3')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument("--disable-extensions")
options.add_experimental_option('useAutomationExtension', False)
options.add_experimental_option("excludeSwitches", ["enable-automation"])
service = Service(ChromeDriverManager().install())

# Initialize WebDriver without the 'desired_capabilities' argument
driver = webdriver.Chrome(service=service, options=options)

driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent":"python 3.11", "platform":"Windows"})


driver.get("https://www.covers.com/sport/basketball/nba/statistics/team-betting/2024-2025")

# Use the 'By' class for locating elements
from selenium.webdriver.common.by import By
element = driver.find_element(By.XPATH, '//*[@id="RegularSeason"]/tbody/tr[1]/td[1]')
print(element.text)

table_body = driver.find_element(By.XPATH, '//*[@id="RegularSeason"]/tbody')

# Get all rows in the table body
rows = table_body.find_elements(By.TAG_NAME, "tr")
max_tr = len(rows)  # Number of rows

# Assuming the first row is representative of the column structure
max_td = len(rows[0].find_elements(By.TAG_NAME, "td"))  # Number of columns

print("Max rows (tr):", max_tr)
print("Max columns (td):", max_td)

for row in range(1, 31):  # Start from 1 to match XPath indexing
    for col in range(1, 9):  # Start from 1 to match XPath indexing
        # print("Row:", row)
        # print("Column:", col)
        time.sleep(15)
        try:
            element = driver.find_element(By.XPATH, f'//*[@id="RegularSeason"]/tbody/tr[{row}]/td[{col}]')
            print("Text:", element.text)
        except Exception as e:
            print(f"Element not found at row {row}, column {col}: {e}")
