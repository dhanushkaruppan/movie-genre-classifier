import os
import re
import sys
import time
import requests
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

# Configurations
GENRES = ['Comedy', 'Romance', 'Sci-Fi']
IMAGES_PER_GENRE = 1000  # Target count
TARGET_SIZE = (299, 299)
OUTPUT_DIR = "Movie_Posters_IMDb"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

def setup_driver():
    """Sets up Edge WebDriver in headless mode for scraping."""
    options = EdgeOptions()
    options.add_argument("--headless") # Run in background without opening window
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    try:
        driver = webdriver.Edge(options=options)
        return driver
    except Exception as e:
        print(f"Edge driver setup failed: {e}. Attempting standard setup...")
        return webdriver.Edge()

def clean_imdb_url(url):
    """Strips the cropping and resizing suffix from IMDb media URLs for original high-resolution."""
    if not url:
        return None
    cleaned_url = re.sub(r'\._V1_.*\.jpg$', '._V1_.jpg', url)
    return cleaned_url

def get_high_res_urls_with_selenium(driver, genre, target_count):
    """Uses Selenium browser to load the page and extract poster URLs using multiple sorts if needed."""
    movie_data = []
    seen_urls = set()
    
    # Try up to 3 sorting strategies on IMDb to collect enough unique movie posters
    sort_strategies = ["num_votes,desc", "release_date,desc", "user_rating,desc"]
    
    for sort_method in sort_strategies:
        if len(movie_data) >= target_count:
            break
            
        print(f"  Loading IMDb page for {genre} sorted by {sort_method}...")
        url = f"https://www.imdb.com/search/title/?genres={genre.lower()}&title_type=feature&sort={sort_method}"
        driver.get(url)
        time.sleep(4)  # Wait for JavaScript to load content
        
        scroll_attempts = 0
        max_scrolls = 40  # Limit scrolling per query to prevent hang
        
        while len(movie_data) < target_count and scroll_attempts < max_scrolls:
            movies = driver.find_elements(By.CLASS_NAME, "ipc-metadata-list-summary-item")
            print(f"    [Sort: {sort_method}] Found {len(movies)} cards. Unique collected: {len(movie_data)}/{target_count}...")
            
            for movie in movies:
                try:
                    poster_el = movie.find_element(By.CSS_SELECTOR, "img.ipc-image")
                    img_url = poster_el.get_attribute("src")
                    title = poster_el.get_attribute("alt")
                    
                    if img_url and "media-amazon.com" in img_url and img_url not in seen_urls:
                        seen_urls.add(img_url)
                        high_res = clean_imdb_url(img_url)
                        movie_data.append((high_res, title))
                except Exception:
                    continue
                    
            if len(movie_data) >= target_count:
                break
                
            try:
                scroll_attempts += 1
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2.5)
                
                more_button = driver.find_elements(By.CLASS_NAME, "ipc-see-more__button")
                if more_button:
                    driver.execute_script("arguments[0].click();", more_button[0])
                    time.sleep(4)
            except Exception:
                break
                
    print(f"  Successfully extracted {len(movie_data)} high-resolution poster URLs for {genre}.")
    return movie_data[:target_count]

def download_and_process(url, title, save_path):
    """Downloads, validates, resizes, and saves the image."""
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return False
            
        img = Image.open(BytesIO(res.content))
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Resize to target network input
        img = img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
        img.save(save_path, "JPEG", quality=95)
        return True
    except Exception:
        return False

def scrape_genre(driver, genre):
    genre_dir = os.path.join(OUTPUT_DIR, genre)
    os.makedirs(genre_dir, exist_ok=True)
    
    # Extract existing movie titles from file names to prevent downloading duplicates
    existing_files = [f for f in os.listdir(genre_dir) if f.endswith('.jpg')]
    existing_count = len(existing_files)
    if existing_count >= IMAGES_PER_GENRE:
        print(f"Genre '{genre}' is already complete with {existing_count} images.")
        return
        
    # Build a set of cleaned titles we already downloaded
    existing_titles = set()
    for f in existing_files:
        name_part = os.path.splitext(f)[0]
        # remove leading index and underscore (e.g. "23_Inception" -> "inception")
        name_part = re.sub(r'^\d+_', '', name_part)
        existing_titles.add(name_part.lower())
        
    print(f"\n--- Scraping Genre: {genre} ---")
    # Search for slightly more than the target to account for existing duplicates
    target_search = IMAGES_PER_GENRE + 200
    movies = get_high_res_urls_with_selenium(driver, genre, target_search)
    
    # Filter out movies we already have
    filtered_movies = []
    for url, title in movies:
        safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '_')]).strip()
        safe_title = safe_title.replace(' ', '_')[:40]
        
        if safe_title.lower() in existing_titles:
            continue
        filtered_movies.append((url, safe_title))
        
    print(f"  Found {len(movies)} poster links on IMDb. Filtered down to {len(filtered_movies)} brand new unique ones.")
    
    # We only need to download enough new ones to reach IMAGES_PER_GENRE
    needed_count = IMAGES_PER_GENRE - existing_count
    filtered_movies = filtered_movies[:needed_count]
    print(f"  Downloading {len(filtered_movies)} new posters to reach total of {IMAGES_PER_GENRE}...")
    
    count = existing_count
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = []
        for idx, (url, safe_title) in enumerate(filtered_movies):
            # Sequence names using existing count to avoid name collisions
            filename = f"{existing_count + idx + 1}_{safe_title}.jpg"
            save_path = os.path.join(genre_dir, filename)
            
            futures.append(executor.submit(download_and_process, url, safe_title, save_path))
            
        for future in futures:
            if future.result():
                count += 1
                if count >= IMAGES_PER_GENRE:
                    break
                    
    print(f"Finished {genre}! Total images: {count}")

def main():
    print(f"Target Directory: '{OUTPUT_DIR}'")
    for genre in GENRES:
        print(f"\nInitializing fresh Selenium Edge WebDriver for: {genre}...")
        driver = setup_driver()
        try:
            scrape_genre(driver, genre)
        finally:
            driver.quit()
    print("\nAll genres processed. WebDriver shut down successfully.")

if __name__ == "__main__":
    main()
