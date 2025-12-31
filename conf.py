# conf.py
import os
from dotenv import load_dotenv
load_dotenv()

# LM Studio のOpenAI互換サーバ
BASE_URL = os.environ.get("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
MODEL_ID = os.environ.get("LMSTUDIO_MODEL_ID", "openai/gpt-oss-20b")

# 互換APIは通常APIキー不要
APIKEY = os.environ.get("DUMMY_API_KEY", "not-needed")
