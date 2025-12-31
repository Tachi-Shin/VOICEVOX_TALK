# chat.py
import requests
import re
from typing import List, Dict
from conf import BASE_URL, MODEL_ID, APIKEY

META_PATTERNS = [
    r"^(?:User says.*)$",
    r"^(?:We should.*)$",
    r"^(?:Need to.*)$",
]
JP_CHAR = r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]"  # かな/カナ/CJK

def sanitize_reply(text: str) -> str:
    # 1) 典型メタ行を「行頭にある分だけ」削除
    for pat in META_PATTERNS:
        text = re.sub(pat, "", text, flags=re.IGNORECASE | re.MULTILINE).strip()
    # 2) 先頭の英数字・英語メタを丸ごと落とし、日本語の最初の文字から切り出す
    m = re.search(JP_CHAR, text)
    if m:
        text = text[m.start():].strip()
    # 3) 長すぎ防止＆空文字フォールバック
    text = text.strip()
    return text or "了解しました。どのようにお手伝いできますか？"

def chat(messages: List[Dict[str, str]]) -> str:
    url = f"{BASE_URL}/chat/completions"
    payload = {
    "model": MODEL_ID,
    "messages": messages,
    "temperature": 0.8,   # ↑ ランダム性アップ
    "top_p": 0.95,
    "max_tokens": 256,
    "stop": ["\nUser says", "\nWe should", "\nNeed to"],
    "stream": False,
}

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {APIKEY}"}
    resp = requests.post(url, json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    raw = data["choices"][0]["message"]["content"]
    return sanitize_reply(raw)
