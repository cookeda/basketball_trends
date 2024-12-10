# %%
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import os

# %%
options = Options()
options.add_argument('--headless')
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument('log-level=3')
service = Service(ChromeDriverManager().install())

# Initialize WebDriver
driver = webdriver.Chrome(service=service, options=options)

# %%
driver.get("https://www.teamrankings.com/nba/trends/ats_trends/")

# %%
# Use the 'By' class for locating elements
from selenium.webdriver.common.by import By
element = driver.find_element(By.XPATH, "/html/body/div[3]/div[1]/div[3]/h1")
print(element.text)

# %%
