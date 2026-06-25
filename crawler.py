import os
from dotenv import load_dotenv
from datetime import datetime, date, timedelta
from supabase import create_client
from google_play_scraper import reviews, Sort
from postgrest.exceptions import APIError

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app_data = supabase.table("apps").select("app_id,app_name,package,cat_id,source_id").execute()
if not app_data.data:
    print("App not found in database.")
    exit(1)

# Calculate yesterday's date
yesterday = date.today() - timedelta(days=1)

rows = []

# Crawl reviews for each app
for app_info in app_data.data:
    APP_NAME = app_info["app_name"]
    APP_ID = app_info["package"]
    APP_TYPE = app_info["cat_id"]
    SOURCE = app_info["source_id"]
    
    print(f"Crawling reviews for {APP_NAME}...")
    
    result, continuation_token = reviews(
        APP_ID,
        lang="id",
        country="id",
        sort=Sort.NEWEST,
        count=10
    )

    for item in result:
        review_text = (item.get("content") or "").strip()
        if len(review_text) < 1:
            continue

        # Filter reviews from D-1 (yesterday) only
        review_date = item["at"].date()
        print(item)
        print("===")
        rows.append({
            "date": item["at"].isoformat(),
            "id": item["reviewId"],
            "score": item["score"],
            "text": review_text,
            "thumbsUp": item["thumbsUpCount"],
            "userName": item["userName"],
            "version": item["appVersion"],
            "replyDate": item["repliedAt"].isoformat() if item["repliedAt"] else None,
            "replyText": item["replyContent"],
            "app_name": APP_NAME,
            "app_type": APP_TYPE,
            "source": SOURCE,
            "review_date": item["at"].date().isoformat(),
            "review_year": item["at"].year,
            "quarter": (item["at"].month - 1) // 3 + 1
        })
    
# Insert all collected reviews once at the end
if rows:
    try:
        supabase.table("reviews").insert(rows).execute()
        print(f"Inserted {len(rows)} reviews (final batch).")
    except APIError as e:
        if "duplicate key" in str(e):
            print(f"Duplicate key found. Inserting non-duplicate reviews...")
            inserted = 0
            skipped = 0
            for row in rows:
                try:
                    supabase.table("reviews").insert([row]).execute()
                    inserted += 1
                except APIError as dup_err:
                    if "duplicate key" in str(dup_err):
                        skipped += 1
                    else:
                        raise
            print(f"Inserted {inserted} reviews, skipped {skipped} duplicates.")
        else:
            raise
else:
    print("No reviews found.")
