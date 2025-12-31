# whisper.py
from io import BytesIO
import os
import speech_recognition as sr
from faster_whisper import WhisperModel

# ==== 設定（必要に応じて変更）====
ASR_MODEL = os.environ.get("ASR_MODEL", "small")  # "small" | "medium" | "large-v3-turbo" など
ASR_DEVICE = os.environ.get("ASR_DEVICE", "cpu")  # "cuda" or "cpu"
ASR_COMPUTE = os.environ.get("ASR_COMPUTE", "int8" if ASR_DEVICE == "cpu" else "float16")
VAD_FILTER = True

# ==== モデル初期化（1回だけ）====
_model = WhisperModel(ASR_MODEL, device=ASR_DEVICE, compute_type=ASR_COMPUTE)

# ==== マイク設定 ====
r = sr.Recognizer()
r.dynamic_energy_threshold = True
r.energy_threshold = 200
r.pause_threshold = 0.4
r.non_speaking_duration = 0.2

def get_audio_from_mic():
    with sr.Microphone(sample_rate=16000) as source:
        print("なにか話してください")
        # 発話開始を待つ最大時間: 2秒 / 1フレーズ最大: 4秒
        audio = r.listen(source, timeout=2, phrase_time_limit=4)
        print("考え中...")
        return audio

def voice_to_text() -> str:
    """
    マイク → WAVバイト → faster-whisper で文字起こしして返す。
    """
    audio = get_audio_from_mic()
    wav_bytes = BytesIO(audio.get_wav_data())

    # 速度重視: beam_size=1, 温度フォールバックで精度担保
    segments, info = _model.transcribe(
        wav_bytes, language="ja", vad_filter=VAD_FILTER,
        beam_size=1, temperature=[0.0, 0.2, 0.4]
    )
    text = "".join(seg.text for seg in segments).strip()
    return text
