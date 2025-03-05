import os
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json

with open("config.json", "r") as f:
    config = json.load(f)

APP_NAME = config["app_name"]
APP_ID = config["app_id"]
BASE_DIR = os.path.join(os.getcwd(), "data") 
os.makedirs(BASE_DIR, exist_ok=True)

base_output_folder = f"{APP_NAME}_CSVFiles"
current_date = datetime.utcnow().strftime("%m-%d-%Y")  # Format: MM-DD-YYYY
daily_folder = os.path.join(base_output_folder, current_date)
csv_file = os.path.join(daily_folder, f"{APP_NAME}_ReviewsProcessed_{current_date}.csv")

# ✅ Check if file exists
if not os.path.exists(csv_file):
    print(f"⚠️ Processed CSV file not found: {csv_file}")
    exit()

# ✅ Load CSV data
df = pd.read_csv(csv_file)

# ✅ Ensure 'topics' and 'sentiment' columns have no NaN values
df["topics"] = df["topics"].fillna("")
df["sentiment"] = df["sentiment"].fillna("Unknown")

# ✅ Format 'at' column to DD/MM/YYYY (if it exists)
if "at" in df.columns:
    df["at"] = pd.to_datetime(df["at"], errors="coerce").dt.strftime("%d/%m/%Y")

# ✅ Debug: Print raw data before processing
print("\n📌 Before Processing:")
print(df[["at", "content", "sentiment", "topics"]].head(10))

# ✅ Separate Positive and Negative Topics
def categorize_topics(row):
    if "Positive" in row["sentiment"]:
        return row["topics"], ""  # Assign to Positive, leave Negative blank
    elif "Negative" in row["sentiment"]:
        return "", row["topics"]  # Assign to Negative, leave Positive blank
    else:
        return "", ""  # Default to blank if sentiment is Unknown

df[["Positive", "Negative"]] = df.apply(categorize_topics, axis=1, result_type="expand")

# ✅ Debug: Print processed data
print("\n📌 After Processing:")
print(df[["at", "content", "Positive", "Negative"]].head(10))

# ✅ Convert DataFrame to list format for Google Sheets
data = [df.columns.tolist()] + df.astype(str).values.tolist()

# ✅ Upload to Google Sheets
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "service_account.json")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Google Sheets configuration
SPREADSHEET_ID = "1QrwpxfAQaQph5VC0_ec_h1wpctnVKESEJdV0iNxo81Q"  # Replace with your spreadsheet ID
SHEET_NAME = f"{APP_NAME} Reviews"  # Change to your desired sheet name

try:
    # Authenticate and initialize Google Sheets API
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)

    # Open the spreadsheet and select the correct sheet (worksheet)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet(SHEET_NAME)  # Select the worksheet by name

    # Optional: Clear previous data from the sheet
    sheet.clear()

    # Update data to the selected sheet
    sheet.update(values=data, range_name="A1")

    print(f"✅ Data uploaded successfully from {csv_file} to the '{SHEET_NAME}' sheet!")

except Exception as e:
    print(f"❌ Error uploading data to Google Sheets: {e}")

