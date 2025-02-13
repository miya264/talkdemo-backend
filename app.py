from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv
import time
import sounddevice as sd
import numpy as np
import soundfile as sf
from pathlib import Path
from fastapi.responses import JSONResponse
import io
import tempfile
import glob

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if api_key is None:
    raise ValueError("APIキーが設定されていません")

client = openai.OpenAI(api_key=api_key)
chat_history = {}

audio_output_dir = Path("static/audio")
audio_output_dir.mkdir(parents=True, exist_ok=True)

# 静的ファイルとして音声ファイルを提供
app.mount("/voice", StaticFiles(directory="static/audio"), name="voice")

class AudioRequest(BaseModel):
    session_id: str
    message: str

def record_audio(fs=16000, max_duration=10, silence_threshold=2.0, amplitude_threshold=0.01):
    print("Recording...")
    start_time = time.time()
    recorded_audio = []
    silent_time = 0
    
    with sd.InputStream(samplerate=fs, channels=1) as stream:
        while time.time() - start_time < max_duration:
            data, _ = stream.read(int(fs * 0.1))  # 100msごとにデータ取得
            recorded_audio.append(data)
            
            if np.max(np.abs(data)) < amplitude_threshold:
                silent_time += 0.1
                if silent_time >= silence_threshold:
                    break
            else:
                silent_time = 0
    
    processing_time = time.time() - start_time
    print(f"Recording completed in {processing_time:.2f} seconds")
    
    if not recorded_audio:
        print("Error: No audio data recorded")
        return None
    
    audio_data = np.concatenate(recorded_audio, axis=0)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        sf.write(temp_audio.name, audio_data, fs, format='WAV', subtype='PCM_16')
        file_path = temp_audio.name
    
    print("Audio recorded at:", file_path)
    return file_path

def transcribe(file_path):
    start_time = time.time()
    try:
        if not file_path or not os.path.exists(file_path):
            return ""
        print("Processing audio file:", file_path)
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ja"
            )
        processing_time = time.time() - start_time
        print(f"Transcription completed in {processing_time:.2f} seconds")
        return transcript.text
    except Exception as e:
        print("Transcription Error:", e)
        return ""
    finally:
        os.remove(file_path)

def talkgpt(text):
    start_time = time.time()
    try:
        if not text:
            return None
        speech_file_path = audio_output_dir / f"response_{int(time.time())}.mp3"
        response_audio = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
        )
        response_audio.stream_to_file(str(speech_file_path))
        
        if not os.path.exists(speech_file_path):
            print("Error: Speech file was not saved correctly")
            return None
        
        processing_time = time.time() - start_time
        print(f"TTS completed in {processing_time:.2f} seconds")
        print(f"Speech file saved at: {speech_file_path}")
        return speech_file_path
    except Exception as e:
        print("TTS Error:", e)
        return None

@app.post("/onsei/")
async def onsei():
    start_time = time.time()
    file_path = record_audio()
    if file_path is None:
        return {"error": "音声の録音に失敗しました"}
    result_onsei = transcribe(file_path)
    if not result_onsei:
        return {"error": "音声のテキスト変換に失敗しました"}
    total_time = time.time() - start_time
    print(f"Total time for onsei: {total_time:.2f} seconds")
    return {"transcribed_text": result_onsei}

@app.post("/audio/")
async def audio(request: AudioRequest):
    start_time = time.time()
    session_id = request.session_id
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="メッセージが空です")
    if session_id not in chat_history:
        chat_history[session_id] = []
    chat_history[session_id].append({"role": "user", "content": message})
    print("Sending to OpenAI:", chat_history[session_id])
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": (
                    "あなたは優しく知的なヘルスケアカウンセラーです。\n"
                    "ユーザーの健康に関する悩みを深掘りし、自己理解を促す質問をします。\n"
                    "あなたの役割は、助言をするのではなく、共感しながら適切な質問を通じてユーザーが自分自身について気づきを得ることです。\n"
                    "質問は簡潔で、ユーザーの発言を反映したものにしてください。\n"
                    "心・身体・性的な悩みがどのように関係しているのかを、ユーザーが自分で考えられるようにサポートしてください。\n"
                    "必要に応じて、『それはどんなときに強く感じますか？』『それが続くとどんな影響がありそうですか？』などの質問を活用してください。\n"
                    "最大20往復で終了するように調整してください。"
                )},
                *chat_history[session_id][-10:]
            ],
            stream=True,
        )
        response_text = "".join([chunk.choices[0].delta.content for chunk in response if chunk.choices[0].delta.content])
    except Exception as e:
        print("ChatGPT Error:", e)
        raise HTTPException(status_code=500, detail="AIの応答生成に失敗しました")
    chat_history[session_id].append({"role": "assistant", "content": response_text})
    print("Received from OpenAI:", response_text)
    speech_file_path = talkgpt(response_text)
    total_time = time.time() - start_time
    print(f"Total time for audio processing: {total_time:.2f} seconds")
    if not speech_file_path:
        raise HTTPException(status_code=500, detail="音声生成に失敗しました")
    return JSONResponse({"text": response_text, "audio_url": f"/voice/{speech_file_path.name}"})
