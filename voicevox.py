import requests
import json
import pyaudio
import wave
import io
from time import sleep

BASE_URL = "http://127.0.0.1:50021"  # VOICEVOXエンジン

def post_audio_query(text: str, speaker: int = 1, speed: float = 1.3) -> dict:
    """
    VOICEVOXにaudio_queryを投げて、speedScaleを変更したJSONを返す
    """
    params = {'text': text, 'speaker': speaker}
    res = requests.post(f"{BASE_URL}/audio_query", params=params)
    res.raise_for_status()
    audio_query = res.json()
    audio_query["speedScale"] = speed
    return audio_query

def post_synthesis(audio_query_response: dict, speaker: int = 1) -> bytes:
    """
    audio_queryの結果を元に音声合成してWAVバイナリを返す
    """
    params = {'speaker': speaker}
    headers = {'content-type': 'application/json'}
    audio_query_response_json = json.dumps(audio_query_response)
    res = requests.post(
        f"{BASE_URL}/synthesis",
        data=audio_query_response_json,
        params=params,
        headers=headers
    )
    res.raise_for_status()
    return res.content

def play_wav(wav_file: bytes):
    """
    WAVバイナリをPyAudioで即時再生する
    """
    wr: wave.Wave_read = wave.open(io.BytesIO(wav_file))
    p = pyaudio.PyAudio()
    stream = p.open(
        format=p.get_format_from_width(wr.getsampwidth()),
        channels=wr.getnchannels(),
        rate=wr.getframerate(),
        output=True
    )
    chunk = 1024
    data = wr.readframes(chunk)
    while data:
        stream.write(data)
        data = wr.readframes(chunk)
    sleep(0.2)  # 再生終了の余白
    stream.close()
    p.terminate()

def text_to_voice(text: str, speaker: int = 1, speed: float = 1.3):
    """
    テキストをVOICEVOXで指定速度・話者の音声にして再生
    """
    audio_query = post_audio_query(text, speaker, speed)
    wav_data = post_synthesis(audio_query, speaker)
    play_wav(wav_data)
