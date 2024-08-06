# import libraries
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta, time

# Temporary link
web = "https://www.pinnacle.com/en/baseball/mlb/matchups/#period:0"

# Helper function that converts given date string to datetime object
def format_date(date):
    if "TODAY" in date.text:
        return datetime.combine(datetime.today(), time(0, 0))
    elif "TOMORROW" in date.text:
        return datetime.combine(datetime.today() + timedelta(days=1), time(0, 0))
    else:
        return datetime.strptime(date.find_element(By.TAG_NAME, 'span').text.split(', ', 1)[1], '%b %d, %Y')

"""
get_pin_odds(driver_path)

Scrapes the game time, odds, and team names from pinnacle.com and returns it as a list of game dictionaries

Params:
    driver_path (str): relative path of chromedriver.

Returns:
    List[Dict]: list of dictionary containing game information
    - sorted in order of game time since they are scraped in the order displayed by the website
      which is already sorted
"""
def get_pin_odds(driver_path):

    # Set webdriver options
    driver_options = Options()
    driver_options.add_argument("--headless")
    driver_options.add_argument('log-level=3')
    driver_options.add_argument('window-size=1920x1080')

    # Set up webdriver
    driver = webdriver.Chrome(service=Service(driver_path), options=driver_options)

    # Open URL
    driver.get(web)

    # Wait until webdriver finds content block containing the games
    events = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.contentBlock.square")))

    # list for storing games and their information
    games = []
    
    driver.get_screenshot_as_file("pin.png") # Take screenshot of current page for debugging

    # Get all rows of events and iterate through them
    rows = events.find_elements(By.XPATH, "./*")
    for row in rows:
        # If row is a row containing the date only, set date
        if "dateBar" in row.get_attribute('class'):
            game_datetime = format_date(row)
        
        # Else it either contains the game information or market label (1 x 2, handicap, O/U etc.)
        else:
            game_details = {}

            # Iterate through columns of row to extract 
            columns = row.find_elements(By.XPATH, "./*")
            for col in columns:
                # If column contains metadata (team names and game time)
                if "metadata" in col.get_attribute('class'):
                    # Add team names to dict
                    game_info = col.find_elements(By.TAG_NAME, 'span')
                    game_details['team1'] = game_info[0].text.split('(')[0].strip()
                    game_details['team2'] = game_info[1].text.split('(')[0].strip()

                    # Add time to game_datetime datetime object and add to dict
                    hrs, mins = map(int, game_info[2].text.split(':'))
                    game_details['datetime'] = game_datetime.replace(hour=hrs, minute=mins)
                
                # Else if it contains moneyline odds
                elif "moneyline" in col.get_attribute('class'):
                    # Get odds
                    odds = col.find_elements(By.TAG_NAME, 'span')

                    # Skip if game odds are suspended or unavailable
                    if len(odds) < 2:
                        break

                    # Add win-draw-win odds to dict
                    if len(odds) > 2:
                        game_details['team1_odds'] = float(odds[0].text)
                        game_details['draw'] = float(odds[1].text)
                        game_details['team2_odds'] = float(odds[2].text)

                    # Or add win-win odds to dict
                    else:
                        game_details['team1_odds'] = float(odds[0].text)
                        game_details['team2_odds'] = float(odds[1].text)

                    # Append dict to list
                    games.append(game_details)

                    break # Move to next row as we only want moneyline odds
                    
    driver.quit()

    return games

if __name__ == '__main__':
    print(get_pin_odds(None))