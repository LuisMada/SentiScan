import os
import pandas as pd
import requests
from datetime import datetime
import openai
import json

# Global Variables
with open("config.json", "r") as f:
    config = json.load(f)

os.environ["TOKENIZERS_PARALLELISM"] = "false"
APP_NAME = config["app_name"]
APP_ID = config["app_id"]
OPEN_AI_KEY = config["openai_api_key"]
openai.api_key = OPEN_AI_KEY
HF_API_KEY = config["hf_api_key"]
HF_MODEL = config["hf_model"]

BASE_DIR = os.path.join(os.getcwd(), "data") 
BASE_OUTPUT_FOLDER = f"{APP_NAME}_CSVFiles"
os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(BASE_OUTPUT_FOLDER, exist_ok=True)

CATEGORIES = [
    "Map/ Location", 
    "Payment", 
    "Rider Performance", 
    "Sanitary", 
    "Booking Experience",
    "Promo Code", 
    "Pricing", 
    "Customer Service", 
    "Management", 
    "App Performance", 
    "Generic"
]

# Categorization using OpenAI GPT with RAG
def categorize_with_openai(new_review, retrieved_reviews):
    print("\n🚀 Sending to OpenAI for categorization:")
    print(f"  📝 New Review: {new_review}")

    prompt = f"""
    You are a classification AI that categorizes customer reviews based on predefined categories.

    **Task:**
    - Read the following new customer review.
    - Assign **all relevant** categories from the given list.

    **Predefined Categories:**
    {", ".join(CATEGORIES)}

    **New Customer Review:**
    "{new_review}"

    **Instructions:**
    - If multiple issues exist, list **all relevant** categories.
    - Return them as a **comma-separated list** (e.g., "Payment, App Performance").
    - Do not include extra text.

    **Output Example:**
    "Payment, App Performance"
    """

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    topics = response["choices"][0]["message"]["content"].strip().split(", ")
    valid_topics = [topic for topic in topics if topic in CATEGORIES]

    if not valid_topics:
        print(f"⚠️ OpenAI returned invalid categories: {topics}. Defaulting to 'Generic'.")
        return "Generic"

    print(f"  ✅ OpenAI Categorized as: {', '.join(valid_topics)}\n")
    return ", ".join(valid_topics)

# Sentiment Analysis
def analyze_sentiment(text):
    url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": text}

    try:
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        
        if "error" in result:
            print(f"⚠️ API Error: {result['error']}")
            return "Unknown"

        sentiments = {s["label"]: s["score"] for s in result[0]}
        sorted_sentiments = sorted(sentiments.items(), key=lambda x: x[1], reverse=True)
        non_neutral = [(sent, score) for sent, score in sorted_sentiments if sent.lower() != "neutral"]
        return non_neutral[0][0].capitalize() if non_neutral else "Positive"
    except Exception as e:
        print(f"❌ Sentiment Analysis Error: {str(e)}")
        return "Unknown"

# Main Processing Function
def process_reviews():
    current_date = datetime.utcnow().strftime("%m-%d-%Y")
    daily_folder = os.path.join(BASE_OUTPUT_FOLDER, current_date)
    if not os.path.exists(daily_folder):
        print(f"⚠️ No folder found for today's reviews: {daily_folder}")
        return

    output_csv_path = os.path.join(daily_folder, f"{APP_NAME}_ReviewsProcessed_{current_date}.csv")
    raw_files = [f for f in os.listdir(daily_folder) if f.startswith(f"{APP_NAME}_Reviews_") and not f.endswith("Processed.csv")]

    if not raw_files:
        print(f"⚠️ No raw review files found in {daily_folder}.")
        return

    for file in raw_files:
        input_csv_path = os.path.join(daily_folder, file)
        df = pd.read_csv(input_csv_path)

        if "content" not in df.columns:
            print(f"❌ Error: Missing 'content' column in {file}.")
            continue

        if df.empty:
            print(f"⚠️ No reviews to process in {file}.")
            continue

        print(f"📄 Processing {len(df)} reviews from {file}...")

        # Analyze sentiment for each review
        df["sentiment"] = df["content"].apply(analyze_sentiment)
        
        # Since similarity retrieval is removed, pass an empty list for retrieved reviews
        df["topics"] = df["content"].apply(lambda x: categorize_with_openai(x, []))

        # Save the processed reviews to CSV
        df.to_csv(output_csv_path, index=False, encoding="utf-8")
        print(f"✅ Finished processing {len(df)} reviews from {file}. Saved to CSV.")

if __name__ == "__main__":
    process_reviews()
