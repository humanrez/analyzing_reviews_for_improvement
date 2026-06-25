from dotenv import load_dotenv
import os
import time
from supabase import create_client
from anthropic import Anthropic


load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in the environment.")

if not ANTHROPIC_API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY must be set in the environment.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = Anthropic(api_key=ANTHROPIC_API_KEY)

def classify_sentiment_with_claude(text: str) -> str:
    """
    Mengklasifikasikan review ke salah satu label: positive, negative, atau neutral.
    """

    if not text or not text.strip():
        return "neutral"

    prompt = f"""
Klasifikasikan teks ulasan berikut ke dalam satu label saja: positive, negative, atau neutral.

Makna label:
- positive: menunjukkan kepuasan, rasa senang, atau apresiasi.
- negative: menunjukkan kekecewaan, ketidakpuasan, atau keluhan.
- neutral: tidak jelas menunjukkan kepuasan atau ketidakpuasan, atau hanya menyampaikan informasi tanpa penilaian emosional.

Jawab hanya dengan salah satu kata: positive, negative, atau neutral.

Teks:
{text}
"""

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=100,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    label = response.content[0].text.strip().lower()
    if label not in {"positive", "negative", "neutral"}:
        return "neutral"

    return label


def get_pending_reviews(limit: int = 3):
    """
    Mengambil review yang masih menunggu klasifikasi sentimen.
    """

    response = (
        supabase
        .table("reviews")
        .select("id,normalized_text")
        .eq("sentiment_classification", "pending")
        .neq("normalized_text", "")
        .eq("lexical_normalization", "done")
        .limit(limit)
        .execute()
    )

    return response.data


def update_sentiment_classification(review_id: int, sentiment: str):
    """
    Menyimpan hasil klasifikasi sentimen ke Supabase.
    """

    supabase.table("reviews").update({
        "sentiment": sentiment,
        "sentiment_classification": "done"
    }).eq("id", review_id).execute()


def main():
    reviews = get_pending_reviews(limit=3)

    if not reviews:
        print("No pending sentiment reviews found.")
        return

    print(f"Found {len(reviews)} pending review(s).")

    for review in reviews:
        review_id = review["id"]
        review_text = review.get("normalized_text") or ""

        if not review_text.strip():
            print(f"Review {review_id} has empty text. Skipping.")
            continue

        try:
            sentiment = classify_sentiment_with_claude(review_text)
            update_sentiment_classification(review_id, sentiment)

            print(f"Review {review_id} classified as {sentiment}.")

            time.sleep(1)

        except Exception as e:
            print(f"Failed to classify review {review_id}: {e}")


if __name__ == "__main__":
    main()