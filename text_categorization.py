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

def classify_text_with_claude(text: str) -> str:
    """
    Mengklasifikasikan review ke salah satu label: usability, credibility, appearance, atau business.
    """

    if not text or not text.strip():
        return "usability"

    prompt = f"""
Klasifikasikan teks ulasan berikut ke dalam satu label saja: usability, credibility, appearance, atau business.

Makna label:
- usability: terkait kemudahan penggunaan, fitur, performa aplikasi, atau pengalaman interaksi.
- credibility: terkait keamanan konsistensi data, kestabilan, atau kualitas layanan yang dipercaya.
- appearance: terkait tampilan, desain, animasi, antarmuka, warna, atau estetika.
- business: terkait harga, promo, bisnis, layanan pelanggan, atau nilai bisnis secara umum.

Jawab hanya dengan salah satu kata: usability, credibility, appearance, atau business.

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
    if label not in {"usability", "credibility", "appearance", "business"}:
        return "usability"

    return label


def get_pending_reviews():
    """
    Mengambil review yang masih menunggu kategorisasi teks.
    """

    response = (
        supabase
        .table("reviews")
        .select("id,normalized_text")
        .eq("sentiment_classification", "done")
        .eq("text_categorization", "pending")
        .neq("normalized_text", "")
        .execute()
    )

    return response.data


def update_text_categorization(review_id: int, category: str):
    """
    Menyimpan hasil kategorisasi teks ke Supabase.
    """

    supabase.table("reviews").update({
        "category": category,
        "text_categorization": "done"
    }).eq("id", review_id).execute()


def main():
    reviews = get_pending_reviews()

    if not reviews:
        print("No pending text categorization reviews found.")
        return

    print(f"Found {len(reviews)} pending review(s).")

    for review in reviews:
        review_id = review["id"]
        review_text = review.get("normalized_text") or ""

        if not review_text.strip():
            print(f"Review {review_id} has empty text. Skipping.")
            continue

        try:
            category = classify_text_with_claude(review_text)
            update_text_categorization(review_id, category)

            print(f"Review {review_id} categorized as {category}.")

            time.sleep(1)

        except Exception as e:
            print(f"Failed to categorize review {review_id}: {e}")


if __name__ == "__main__":
    main()