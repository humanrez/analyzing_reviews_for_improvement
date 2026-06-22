import os
from dotenv import load_dotenv
from datetime import datetime, date, timedelta
from supabase import create_client
from google_play_scraper import reviews, Sort

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

APP_NAME = "Livin by Mandiri"
APP_ID = "id.bmri.livin"
APP_TYPE = "Digital Bank"
SOURCE = "Google Play"

result, continuation_token = reviews(
    APP_ID,
    lang="id",
    country="id",
    sort=Sort.NEWEST,
    count=15
)

print("Today:")
print(date.today())

# Calculate yesterday's date
yesterday = date.today() - timedelta(days=1)

print("Yesterday:")
print(yesterday)

rows = []

for item in result:
    # Filter reviews from D-1 (yesterday) only
    review_date = item["at"].date()
    if review_date != yesterday:
        continue
    
    print(item)
    print("===")
    rows.append({
        "date": item["at"].isoformat(),
        "id": item["reviewId"],
        "score": item["score"],
        "text": item["content"],
        "thumbsUp": item["thumbsUpCount"],
        "userName": item["userName"],
        "version": item["appVersion"],
        "replyDate": item["repliedAt"].isoformat() if item["repliedAt"] else None,
        "replyText": item["replyContent"],
        "app_name": APP_NAME,
        "app_type": APP_TYPE,
        "source": SOURCE
    })

if rows:
    supabase.table("reviews").insert(rows).execute()
    print(f"Inserted {len(rows)} reviews.")
else:
    print("No reviews found.")