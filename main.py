from chat import chat
from whisper import voice_to_text
from voicevox import text_to_voice

def get_user_text() -> str:
    """
    文字入力があればそれを採用。空Enterなら音声入力にフォールバック。
    """
    try:
        typed = input(">> テキスト入力（空Enterで音声入力）：").strip()
    except EOFError:
        typed = ""
    if typed:
        return typed
    # 空Enter → 音声
    return voice_to_text().strip()

def trim_messages(messages, keep_last=8):
    if len(messages) <= keep_last:
        return messages
    summary_text = summarize_old_messages(messages[:-keep_last])
    return messages[:1] + [
        {"role": "system", "content": f"ここまでの会話要約:\n{summary_text}"}
    ] + messages[-keep_last:]

def summarize_old_messages(old_msgs):
    """
    古い履歴を短い文章にまとめる関数。
    今はダミー実装だが、後でchat()を使って要約させても良い。
    """
    texts = []
    for m in old_msgs:
        if m["role"] in ("user", "assistant"):
            texts.append(f"{m['role']}: {m['content']}")
    return " / ".join(texts[:5]) + ("..." if len(texts) > 5 else "")

def main():
    messages = [
        {
            'role': 'system',
            'content': (
                "あなたは礼儀正しい日本語アシスタントですが、会話の雰囲気に応じて柔軟に対応します。"
                "ボケ・ツッコミやネタには乗り、ユーモアを交えた返答をしてください。"
                "途中で無難な定型文に戻らず、会話の流れとキャラクターを維持してください。"
                "内部の思考や方針は出力せず、日本語のみで返答してください。"
            )
        }
    ]

    try:
        while True:
            text = get_user_text()
            if not text.strip():
                continue

            # ユーザー発話を履歴に追加
            messages.append({"role": "user", "content": text})
            
            # 履歴を短縮して送信
            messages_to_send = trim_messages(messages, keep_last=8)

            # モデルからの応答
            response = chat(messages_to_send)

            # モデルの返答を履歴に追加
            messages.append({"role": "assistant", "content": response})

            print(f'User   : {text}')
            print(f'LM-OSS : {response}')
            text_to_voice(response)

    except KeyboardInterrupt:
        print("\n[INFO] ユーザー操作により終了しました。")

if __name__ == '__main__':
    main()
