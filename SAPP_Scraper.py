import os
import time
import json
import pandas as pd
from datetime import datetime, timedelta
from google_play_scraper import reviews, Sort

# App ID for Angkas
with open("config.json", "r") as f:
    config = json.load(f)

APP_NAME = config["app_name"]
APP_ID = config["app_id"]
TIME_TO_SCRAPE = config["time_to_scrape"]
BASE_DIR = os.path.join(os.getcwd(), "data")
BASE_OUTPUT_FOLDER = f"{APP_NAME}_CSVFiles"
os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(BASE_OUTPUT_FOLDER, exist_ok=True)
TIMESTAMP_FILE = os.path.join(BASE_OUTPUT_FOLDER, "last_scraped.txt")

# Check if date_range is provided in config
date_range = config.get("date_range")
if date_range:
    try:
        start_date = datetime.fromisoformat(date_range[0])
        end_date = datetime.fromisoformat(date_range[1]) if len(date_range) > 1 else datetime.utcnow()
        last_scraped_time = start_date  # Override last_scraped_time with user-defined start date
        print(f"📅 Fetching reviews from {start_date} to {end_date}")
    except ValueError:
        print("⚠️ Invalid date format in config. Using default behavior.")
        last_scraped_time = None
else:
    # Original behavior
    try:
        with open(TIMESTAMP_FILE, "r") as f:
            last_scraped_time_str = f.read().strip()
            last_scraped_time = datetime.fromisoformat(last_scraped_time_str) if last_scraped_time_str else None
    except (FileNotFoundError, ValueError):
        last_scraped_time = None

    if last_scraped_time is None:
        last_scraped_time = datetime.utcnow() - timedelta(hours=TIME_TO_SCRAPE)
        print(f"📅 No last timestamp found. Fetching reviews from the last 24 hours.")

# Generate a date-specific folder
current_date = datetime.utcnow().strftime("%m-%d-%Y")  # Format: MM-DD-YYYY
daily_folder = os.path.join(BASE_OUTPUT_FOLDER, current_date)
os.makedirs(daily_folder, exist_ok=True)  # Create folder for today's reviews if it doesn't exist

# Generate filename with current timestamp (MM-DD-YYYY_HH-MM-SS)
current_datetime = datetime.utcnow().strftime("%m-%d-%Y_%H-%M-%S")
csv_file_path = os.path.join(daily_folder, f"{APP_NAME}_Reviews_{current_datetime}.csv")

# List to store new reviews
new_reviews = []
count = 400  # Fetch batch size
continuation_token = None  # Used for pagination

while True:
    # Fetch reviews sorted by newest first
    result, continuation_token = reviews(
        APP_ID,
        lang=None,       # Fetch reviews in all languages
        country="ph",    # Fetch from the Philippines
        sort=Sort.NEWEST,  # Sort by newest
        count=count,     # Fetch 200 reviews at a time
        continuation_token=continuation_token  # Continue pagination
    )

    if not result:
        print("⚠️ No reviews found.")
        break

    # Debugging: Print first review's timestamp
    print(f"First review fetched: {result[0]['at']} UTC")

    # Track newest timestamp
    latest_timestamp = last_scraped_time

    # Filter new reviews
    for review in result:
        review_date = review["at"]

        # Stop if we reach a previously scraped review
        if last_scraped_time is not None and review_date <= last_scraped_time:
            print(f"⏹️ Stopping at review dated {review_date} (already scraped).")
            break  # Stop fetching

        new_reviews.append(review)
        if latest_timestamp is None or review_date > latest_timestamp:
            latest_timestamp = review_date  # Update latest timestamp

    print(f"✅ {len(new_reviews)} new reviews collected so far...")

    # Stop if no more reviews or we've reached already scraped data
# Stop if we've reached the user-defined end date
    if continuation_token is None or (last_scraped_time is not None and review_date <= last_scraped_time) or (date_range and review_date < start_date):
        break


    time.sleep(2)  # Avoid hitting the server too fast

# Save new reviews only if data exists
if new_reviews:
    df = pd.DataFrame(new_reviews)[["userName", "score", "at", "content"]]
    df.to_csv(csv_file_path, index=False, encoding="utf-8")
    print(f"✅ Saved {len(df)} total reviews to {csv_file_path}")

    # Update last scraped timestamp (OUTSIDE date folders)
    with open(TIMESTAMP_FILE, "w") as f:
        f.write(latest_timestamp.isoformat())
    print(f"📌 Updated last scraped timestamp: {latest_timestamp}")

else:
    print("⚠️ No new reviews to save.")
