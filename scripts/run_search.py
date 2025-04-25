
import json
import os
import time
import requests
from bs4 import BeautifulSoup
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
        "num": 10
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def fetch_webpage_text(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        return f"[本文取得失敗: {e}]"

def gemini_summarize(texts):
    prompt = f"以下の複数のWebページ本文から、大阪万博における各国パビリオンの参加状況を要約してください：\n\n{texts}"
    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
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
    os.makedirs("data/html_texts", exist_ok=True)
    os.makedirs("_posts", exist_ok=True)

    result_log = []

    for country in countries:
        query = f"{country} パビリオン 大阪万博"
        log(f"検索中: {query}")

        try:
            search_result = google_search(query)
            body_texts = ""
            html_text_entry = {}
            links_info = []

            for item in search_result.get("items", []):
                url = item["link"]
                title = item["title"]
                log(f"本文取得: {url}")
                page_text = fetch_webpage_text(url)
                html_text_entry[title] = {
                    "url": url,
                    "text": page_text[:5000]  # 長すぎる本文を制限
                }
                body_texts += f"【{title}】\n{page_text[:1000]}\n\n"
                links_info.append({"title": title, "link": url})

            gemini_summary = gemini_summarize(body_texts)

            # JSONログ出力
            result_entry = {
                "timestamp": datetime.now().isoformat(),
                "country": country,
                "query": query,
                "links": links_info,
                "gemini_summary": gemini_summary
            }
            result_log.append(result_entry)

            # Markdown出力
            date_prefix = datetime.now().strftime("%Y-%m-%d")
            md_filename = f"_posts/{date_prefix}-{country}.md"
            with open(md_filename, "w", encoding="utf-8") as f:
                f.write(f"# {country}のパビリオン状況（大阪万博）\n\n")
                f.write(f"**検索クエリ：** {query}\n\n")
                for link in links_info:
                    f.write(f"- [{link['title']}]({link['link']})\n")
                f.write(f"\n\n---\n\n**Gemini要約：**\n\n{gemini_summary}\n")

            # BeautifulSoupのテキスト抽出結果を保存
            with open(f"data/html_texts/{country}.json", "w", encoding="utf-8") as f:
                json.dump(html_text_entry, f, ensure_ascii=False, indent=2)

            log(f"出力完了: {md_filename}")
            time.sleep(2)

        except Exception as e:
            log(f"エラー（{country}）: {str(e)}")

    with open("data/results/result.json", "w", encoding="utf-8") as f:
        json.dump(result_log, f, ensure_ascii=False, indent=2)

    log("全処理完了")

if __name__ == "__main__":
    main()
