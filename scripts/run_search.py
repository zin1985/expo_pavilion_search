import json, os, time
import requests
from datetime import datetime

GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
GOOGLE_CX = os.environ["GOOGLE_CX"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

def google_search(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": query,
        "num": 3
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def gemini_summarize(texts):
    prompt = f"以下の検索結果から、大阪万博におけるパビリオンの参加状況を要約してください：\n\n{texts}"
    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
        params={"key": GEMINI_API_KEY},
        json={"contents": [{"parts": [{"text": prompt}]}]}
    )
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]

def log(message):
    print(f"[LOG] {message}")

def main():
    with open("data/countries.json", encoding="utf-8") as f:
        countries = json.load(f)

    os.makedirs("data/results", exist_ok=True)
    os.makedirs("_posts", exist_ok=True)

    result_log = []

    for country in countries:
        query = f"{country} パビリオン 大阪万博"
        log(f"検索中: {query}")

        try:
            search_result = google_search(query)
            snippets = "\n\n".join(item["snippet"] for item in search_result.get("items", []))
            gemini_result = gemini_summarize(snippets)

            result_entry = {
                "timestamp": datetime.now().isoformat(),
                "country": country,
                "query": query,
                "search_result": search_result
            }
            result_log.append(result_entry)

            date_prefix = datetime.now().strftime("%Y-%m-%d")
            md_filename = f"_posts/{date_prefix}-{country}.md"
            with open(md_filename, "w", encoding="utf-8") as f:
                f.write(f"# {country}のパビリオン状況（大阪万博）\n\n")
                f.write(f"**検索クエリ：** {query}\n\n")
                f.write(f"**Gemini要約：**\n\n{gemini_result}\n")

            log(f"生成完了: {md_filename}")
            time.sleep(2)

        except Exception as e:
            log(f"エラー発生（{country}）: {str(e)}")

    with open("data/results/result.json", "w", encoding="utf-8") as f:
        json.dump(result_log, f, ensure_ascii=False, indent=2)

    log("全処理完了")

if __name__ == "__main__":
    main()
