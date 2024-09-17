from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd
import argparse
from datetime import datetime
import time

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scrape_site(site_id, date, num_people=4):
    url = f"https://www.recreation.gov/permits/{site_id}/registration/detailed-availability?date={date}"
    
    driver = setup_driver()
    #print(f"Fetching URL: {url}")

    driver.get(url)
    #print(f"Got URL: {url}")

    try:
        #print("Waiting for page to load...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        #print("Locating 'Add Group Members' dropdown...")
        dropdown = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "guest-counter-QuotaUsageByMemberDaily"))
        )
        
        #print("Clicking 'Add Group Members' dropdown...")
        dropdown.click()

       #print(f"Setting number of people to {num_people}...")
        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "guest-counter-QuotaUsageByMemberDaily-number-field-People-and-Pets"))
        )
        input_field.clear()
        input_field.send_keys(str(num_people))

        #print("Closing the dropdown...")
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@data-component='DropdownBase-actions']//button[.//span[text()='Close']]"))
        )
        #print("Found close button")
        close_button.click()
        #print("Clicked close button")

        #print("We updated the number of people successfully!! Table should be visible now")

        #print("Waiting for table to load...")
        table = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "per-availability-table"))
        )

        #print("Got table! Now Searching for rows")

        # Find all rows in the table
        rows = table.find_elements(By.CLASS_NAME, "rec-grid-row")

        #print("Got rows (Campsites)")

        all_sites = []
        available_sites = []
        print("Checking availability of {} rows (Campsites)".format(len(rows)))

        for row in rows:
            try:
                # Get the site name
                site_name = row.find_element(By.XPATH, ".//button[contains(@class, 'sarsa-button-link')]/span/span").text
                
                all_sites.append(site_name)
                #print("Checking Site: ", site_name)
                #site_name = row.find_element(By.XPATH, ".//button[contains(@class, 'sarsa-button-link')]/span/span").text
                #print(f"Checking site: {site_name}")

                #availability_cells = row.find_elements(By.XPATH, ".//div[@data-testid='availability-cell']")

                # Find the first availability cell
                first_availability_cell = row.find_elements(By.CLASS_NAME, "rec-grid-grid-cell")[1]  # The second cell in the row

                # Check if the first availability cell is available
                if "unavailable" not in first_availability_cell.get_attribute("class"):
                    available_sites.append(site_name)
                    print("Site {} is available".format(site_name))
                    #print(f"Site {i} is available")

                else:
                    pass
                    #print(f"{i} is not available")

            except Exception as e:
                print(f"Error processing row: {str(e)}")

        df = pd.DataFrame({
            'Campsite': all_sites,
            'Availability': ['Unavailable'] * len(all_sites)
        })
        for ind, row in df.iterrows():
            if row['Campsite'] in available_sites:
                df.at[ind, 'Availability'] = 'Available'
        
        print(f"Created DataFrame with {len(available_sites)} available sites")        
        return df

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print(f"Current URL: {driver.current_url}")
        print(f"Page source: {driver.page_source[:500]}...")  # Print first 500 characters of page source
        return None#pd.DataFrame(columns=['Campsite', 'Availability'])
    
    finally:
        driver.quit()

def main():
    parser = argparse.ArgumentParser(description="Scrape recreation.gov for campsite availability.")
    parser.add_argument("site_id", help="The site ID to scrape")
    parser.add_argument("date", help="The date to check (YYYY-MM-DD)")
    args = parser.parse_args()

    try:
        datetime.strptime(args.date, '%Y-%m-%d')
    except ValueError:
        print("Error: Date must be in YYYY-MM-DD format")
        return

    print(f"Scraping site {args.site_id} for date {args.date}")
    result = scrape_site(args.site_id, args.date)
    
    if result is None:
        print("No availability information found.")
        
    else:
        print("\nFinal Results:")
        print(result)
        
        csv_filename = f"availability_{args.site_id}_{args.date}.csv"
        result.to_csv(csv_filename, index=False)
        print(f"\nResults saved to {csv_filename}")

if __name__ == "__main__":
    main()