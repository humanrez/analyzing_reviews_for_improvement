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

def normalize_text_with_claude(text: str) -> str:
    """
    Mengubah review informal menjadi Bahasa Indonesia baku.
    """

    if not text or not text.strip():
        return ""

    prompt = f"""
Tulis ulang teks berikut ke dalam Bahasa Indonesia yang baku, jelas, dan natural.

Aturan:
- Jangan mengubah makna asli.
- Jangan menambahkan informasi baru.
- Jangan menghapus keluhan utama.
- Perbaiki typo, singkatan, slang, dan bahasa informal.
- Hilangkan emoji dan tanda baca
- Jika teks berisi campuran bahasa Indonesia dan Inggris, pertahankan istilah teknis yang umum digunakan.
- Berikan hanya hasil teks yang sudah dinormalisasi, tanpa penjelasan tambahan.

Teks:
{text}
"""

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=300,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.content[0].text.strip()


def get_unnormalized_reviews(limit: int = 13):
    """
    Mengambil review yang belum punya normalized_text.
    """

    response = (
        supabase
        .table("reviews")
        .select("id,text")
        .eq("lexical_normalization", "pending")
        .limit(limit)
        .execute()
    )

    return response.data


def update_normalized_text(review_id: int, normalized_text: str):
    """
    Menyimpan hasil normalisasi ke Supabase.
    """

    supabase.table("reviews").update({
        "normalized_text": normalized_text,
        "lexical_normalization": "done"
    }).eq("id", review_id).execute()


def main():
    reviews = get_unnormalized_reviews(limit=13)

    if not reviews:
        print("No unnormalized reviews found.")
        return

    print(f"Found {len(reviews)} unnormalized reviews.")

    for review in reviews:
        review_id = review["id"]
        review_text = review.get("text") or ""

        if not review_text.strip():
            print(f"Review {review_id} has empty text. Skipping.")
            continue

        try:
            normalized_text = normalize_text_with_claude(review_text)
            update_normalized_text(review_id, normalized_text)

            print(f"Review {review_id} normalized.")

            # jeda kecil agar tidak terlalu agresif memanggil API
            time.sleep(1)

        except Exception as e:
            print(f"Failed to normalize review {review_id}: {e}")


if __name__ == "__main__":
    main()