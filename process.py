# launcher.py
# Windows向け: VOICEVOX と LM Studio を起動し、API待機・モデル確認・事前ロード後に main.py を実行
# 事前に: pip install requests

import subprocess
import sys
import time
import json
from pathlib import Path

import requests

# ====== 設定 ======

LM_HOST  = "127.0.0.1"
LM_PORT  = 1234
VV_HOST  = "127.0.0.1"
VV_PORT  = 50021

# /v1/models の id と一致させること
LM_MODEL = "openai/gpt-oss-20b"

# VRAMに合わせて調整 (1050Tiなら 10〜20 程度)
LM_GPU_LAYERS = 12

# ====== ユーティリティ ======
def start_minimized(cmd):
    """
    Windowsで新しいコンソールを最小化して起動。
    失敗しても通常起動にフォールバック。
    """
    startupinfo = None
    creationflags = 0
    try:
        # Windows専用: 最小化
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        SW_MINIMIZE = 6
        startupinfo.wShowWindow = SW_MINIMIZE

        creationflags = subprocess.CREATE_NEW_CONSOLE
    except Exception:
        pass

    return subprocess.Popen(
        cmd,
        startupinfo=startupinfo,
        creationflags=creationflags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=False
    )

def wait_for_http_ok(url: str, timeout_sec_per_try=3, retry_interval=2):
    """
    指定URLが200を返すまで待機。
    Ctrl+Cで中断可能。
    """
    while True:
        try:
            r = requests.get(url, timeout=timeout_sec_per_try)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(retry_interval)

def print_models(base_url: str):
    try:
        data = requests.get(f"{base_url}/v1/models", timeout=5).json()
        ids = [m.get("id") for m in data.get("data", [])]
        print("[INFO] Available models:")
        for mid in ids:
            print("  -", mid)
    except Exception as e:
        print(f"[WARN] Failed to fetch models: {e}")

def preload_model(base_url: str, model_id: str) -> bool:
    """
    chat/completions に最小問い合わせを投げて JIT ロードを誘発。
    """
    headers = {"Content-Type": "application/json"}
    body = {
        "model": model_id,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1
    }
    try:
        r = requests.post(f"{base_url}/v1/chat/completions",
                          headers=headers, data=json.dumps(body), timeout=120)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"[WARN] Model preload failed: {e}")
        return False

def path_exists_or_die(p: str, label: str):
    if not Path(p).exists():
        print(f"[ERROR] {label} not found: {p}")
        sys.exit(1)

def main():
    path_exists_or_die(VV_EXE, "VOICEVOX engine")
    path_exists_or_die(LM_EXE, "LM Studio")
    path_exists_or_die(PY_MAIN, "main.py")

    vv_proc = None
    lm_proc = None

    try:
        # ====== VOICEVOX ENGINE 起動 ======
        print("[INFO] Starting VOICEVOX ENGINE (GPU)...")
        vv_cmd = [
            VV_EXE,
            "--host", VV_HOST,
            "--port", str(VV_PORT),
            "--use_gpu"
        ]
        vv_proc = start_minimized(vv_cmd)

        # ====== LM Studio API サーバ起動 ======
        print("[INFO] Starting LM Studio API server (GPU)...")
        lm_cmd = [
            LM_EXE,
            "--server",
            "--port", str(LM_PORT),
            "--model", LM_MODEL,
            "--gpu_layers", str(LM_GPU_LAYERS),
        ]
        lm_proc = start_minimized(lm_cmd)

        # ====== API待機 ======
        base_url = f"http://{LM_HOST}:{LM_PORT}"
        print(f"[INFO] Waiting for LM Studio API at {base_url} ...")
        wait_for_http_ok(f"{base_url}/v1/models")
        print("[INFO] LM Studio API is up.")

        # ====== モデル一覧表示（任意） ======
        print("[INFO] Checking available models...")
        print_models(base_url)

        # ====== 事前ロード（JITトリガ） ======
        print(f'[INFO] Preloading model "{LM_MODEL}" ...')
        ok = preload_model(base_url, LM_MODEL)
        if ok:
            print("[INFO] Model preloaded successfully.")
        else:
            print("[WARN] Check model id or reduce --gpu_layers")

        # ====== Python アプリ起動 ======
        print("[INFO] Launching main.py ...")
        # main.py 側が LM/VV へ接続する前提
        # 親プロセスは main.py の終了まで待機
        ret = subprocess.call([sys.executable, PY_MAIN])
        print(f"[INFO] main.py exited with code {ret}")

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user.")
    finally:
        # ====== 終了処理 ======
        # 子プロセスを丁寧に終了（先に LM、次に VOICEVOX）
        for name, proc in (("LM Studio", lm_proc), ("VOICEVOX", vv_proc)):
            if proc and proc.poll() is None:
                print(f"[INFO] Terminating {name} ...")
                try:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        print(f"[WARN] {name} did not exit in time. Killing...")
                        proc.kill()
                except Exception as e:
                    print(f"[WARN] Failed to terminate {name}: {e}")

        # Windowsバッチの pause 相当
        try:
            input("Press Enter to exit...")
        except Exception:
            pass

if __name__ == "__main__":
    main()
