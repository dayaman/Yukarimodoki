# https://qiita.com/yukky-k/items/0d18ec22420e8b35d0ac より引用

import pyaudio
import numpy as np
import requests
import json
import sys

CHUNK = 1024 * 2
FORMAT = pyaudio.paInt16  # 16bits
CHANNELS = 1  # モノラル
RATE = 48000  # サンプリングレート
MAX_RECORD_SECONDS = 10 # 最大録音時間
SILENCE_SECONDS = 2 # 無音検知時間
threshold_start = 0.2 # 録音開始の閾値　環境によりけり
threshold_stop = 0.2 # 録音終了の閾値

p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                input_device_index=3)

with open('token.json') as f:
    df = json.load(f)

# メイン
# -----
def main():
    while True:
        mic_input = input_audio()
        text = voice_to_text(mic_input)
        if text == "終了。":
            stream.close()
            p.terminate()
            sys.exit()

def to_text():
    while True:
        mic_input = input_audio()
        text = voice_to_text(mic_input)
        return text
# 音声入力部
# -----
def input_audio():
    frames = []
    buf_old = []
    stream.start_stream()
    while True:
        # 音声入力待ち
        buf = read_stream()
        if buf.max() / 32768 > threshold_start:
            # 音声入力判定されたら録音処理
            print("録音開始")
            frames = recording(buf)
            print("録音終了")
            stream.stop_stream()
            # 一時保存データがあれば先頭に追加
            if len(buf_old) != 0:
                frames.insert(0, b''.join(replacebyte(buf_old)))
            return b''.join(frames)
        # 音声を一時保存
        buf_old = buf
    # 繰り返し

# テキスト変換部
# docomo音声認識APIを利用
# -----
def voice_to_text(audio):
    global df
    APIKEY = df['docomo']
    url = "https://api.apigw.smt.docomo.ne.jp/amiVoice/v1/recognize?APIKEY={}".format(APIKEY)
    files = {"a": audio, "v": "on"}

    r = requests.post(url, files=files)
    json_data = r.json()
    text = json_data['text']
    print(text)
    return text

# 録音
# -----
def recording(buf):
    frames = []
    frames.append(b''.join(replacebyte(buf)))
    cnt = 0
    for i in range(1, int(RATE / CHUNK * MAX_RECORD_SECONDS)):
        buf = read_stream()
        frames.append(b''.join(replacebyte(buf)))
        # 一定時間音声入力が無ければ終了
        cnt = count_silent_frame(cnt, buf)
        if cnt > (RATE / CHUNK * SILENCE_SECONDS): return frames
    return frames

# ストリーム読み込み
# -----
def read_stream():
    data = stream.read(CHUNK)
    buf = downsampling(data)
    return buf

# ダウンサンプリング
# -----
def downsampling(data):
    x = np.frombuffer(data, dtype="int16")
    return x[::3]

# エンディアン変換（上位8bitと下位8bit入れ替え）
# -----
def replacebyte(data):
    z = []
    for i in range(0, int(len(data))):
        x = np.frombuffer(data[i], dtype="int8")
        y = (x[1], x[0])
        z.append(b''.join(y))
    return z

# 無音時間の連続フレーム数カウント
# -----
def count_silent_frame(cnt, buf):
    if buf.max() / 32768 < threshold_stop:
        cnt = cnt + 1
    else:
        cnt = 0
    return cnt

if __name__ == "__main__":
    main()