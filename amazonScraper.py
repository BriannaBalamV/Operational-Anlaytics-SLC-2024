import os
import time
import pandas as pd
import unicodedata
import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from langdetect import detect
from chromedriver_py import binary_path

# Setup the downloads directory
download_dir = r"C:\Users\brian\OneDrive\Documentos\Brianna\St Lawrence College\4 semester\operational analytics"
# Adjust this to your actual full downloads directory path
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# Setup Selenium WebDriver
service = ChromeService(executable_path=binary_path)
options = webdriver.ChromeOptions()
options.add_experimental_option("prefs", {"download.default_directory": download_dir})
driver = webdriver.Chrome(service=service, options=options)

# List to store comments
comments = []

def clean_text(text):
    """
    This function cleans up the text by:
    - Unescaping HTML entities
    - Normalizing Unicode characters
    - Removing non-printable characters and special symbols
    - Replacing special punctuation like smart quotes and apostrophes
    """
    # Unescape HTML entities like &amp;, &quot;, etc.
    text = html.unescape(text)
    
    # Normalize Unicode to remove diacritics and other special combining marks
    text = unicodedata.normalize('NFKD', text)
    
    # Replace special quotes and apostrophes with standard ones
    replacements = {
        "’": "'",  # Smart apostrophe to regular apostrophe
        "“": '"',  # Left double quote to regular quote
        "”": '"',  # Right double quote to regular quote
        "–": "-",  # En dash to regular dash
        "—": "-",  # Em dash to regular dash
        "‘": "'",  # Left single quote to apostrophe
    }
    
    for orig, replacement in replacements.items():
        text = text.replace(orig, replacement)
    
    # Remove non-printable characters
    text = ''.join(c for c in text if unicodedata.category(c)[0] != 'C')
    
    # Return the cleaned text
    return text

def detect_captcha():
    """ Check if the page has a CAPTCHA challenge and pause to allow manual solving. """
    try:
        captcha_element = driver.find_element(By.CSS_SELECTOR, "img[src*='captcha']")
        if captcha_element:
            print("CAPTCHA detected! Please solve the CAPTCHA manually.")
            input("Press Enter after solving the CAPTCHA to continue...")
    except NoSuchElementException:
        print("No CAPTCHA detected.")

def scrape_amazon_comments(url, total_comments=30):
    driver.get(url)
    time.sleep(2)  # Wait for the page to load

    detect_captcha()  # Check for CAPTCHA before starting

    while len(comments) < total_comments:
        # Check for CAPTCHA on each page
        detect_captcha()

        # Find all review elements on the page
        review_elements = driver.find_elements(By.CSS_SELECTOR, '.review-text-content span')
        review_dates = driver.find_elements(By.CSS_SELECTOR, '.review-date')  # Extract review dates
        review_stars = driver.find_elements(By.CSS_SELECTOR, '.review-rating span.a-icon-alt')  # Extract star ratings

        for i, review in enumerate(review_elements):
            if len(comments) >= total_comments:
                break
            comment_text = review.text.strip()
            review_date = review_dates[i].text  # Extract corresponding review date
            review_star = review_stars[i].get_attribute('textContent')  # Extract star rating

            # Detect language, process only English comments
            try:
                if detect(comment_text) == 'en':  # Check if the comment is in English
                    # Clean the text of special symbols and normalize it
                    cleaned_comment = clean_text(comment_text)
                    comments.append({
                        "Comment Number": len(comments) + 1,
                        "Date": review_date,
                        "Rating": review_star,
                        "Comment": cleaned_comment
                    })
                    print(f"Scraped and cleaned comment: {cleaned_comment} - Rating: {review_star}")
            except Exception as e:
                print(f"Error detecting language or cleaning comment: {e}")

        # Click the next page button, if available
        try:
            # Use an explicit wait to ensure the button is present
            next_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li.a-last a')))
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(2)  # Wait for the new page to load
        except (NoSuchElementException, TimeoutException):
            print("No more pages or next button not found. Scraping complete.")
            break  # Exit if no more pages or the next button can't be found

    print(f"Total English comments scraped: {len(comments)}")
    return comments

# URL of the Amazon product review page
url = "https://www.amazon.ca/AmazonBasics-Ear-Headphones-Mic-Black/product-reviews/B07HH1QSLB/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews"

# Start scraping comments
scraped_comments = scrape_amazon_comments(url, total_comments=30)

# Save the comments to a CSV file with improved formatting
df = pd.DataFrame(scraped_comments)
csv_path = os.path.join(download_dir, 'amazon_product_comments_with_ratings.csv')
df.to_csv(csv_path, index=False, columns=["Comment Number", "Date", "Rating", "Comment"])

# Close the browser
driver.quit()

print(f"Comments with ratings have been saved to {csv_path}")
