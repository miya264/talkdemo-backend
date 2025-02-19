from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import openai
import os
from dotenv import load_dotenv
from pathlib import Path
from fastapi.responses import JSONResponse
import mimetypes
import time

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

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

AUDIO_OUTPUT_DIR = Path("static/audio")
AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/voice", StaticFiles(directory="static/audio"), name="voice")

@app.post("/upload-audio/")
async def upload_audio(file: UploadFile = File(...)):
    try:
        file_path = UPLOAD_DIR / file.filename
        temp_file_path = file_path.with_suffix(".webm")

        # 既存のファイルがある場合は削除 (ゴミデータ対策)
        temp_file_path.unlink(missing_ok=True)

        with temp_file_path.open("wb") as buffer:
            buffer.write(await file.read())

        print("✅ ファイル保存成功:", temp_file_path)

        transcribed_text = transcribe_audio(temp_file_path)
        if not transcribed_text:
            print("⚠️ 文字起こしに失敗しました")
            return JSONResponse({"error": "文字起こしに失敗しました"}, status_code=500)

        ai_response, audio_url = generate_ai_response(transcribed_text)
        return {"transcribed_text": transcribed_text, "ai_response": ai_response, "audio_url": f"{audio_url}"}
    
    except Exception as e:
        print("❌ エラー発生:", e)
        return JSONResponse({"error": f"音声アップロードエラー: {str(e)}"}, status_code=500)



def transcribe_audio(file_path: Path):
    try:
        print(f"📄 文字起こしを開始: {file_path}")

        if not file_path.exists():
            print("❌ 音声ファイルが見つかりません")
            return ""

        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        print(f"✅ 文字起こし完了: {transcript.text}")
        return transcript.text
    except Exception as e:
        print("Transcription Error:", e)
        return ""

# 温かみのある会話を実現するプロンプト
SYSTEM_PROMPT = """
あなたは、ユーザーの悩みを受け止め、安心して話せる場を提供する温かみのある対話AIです。
以下の点を意識して会話してください。

1. **相槌を適度に入れる**（例：「うんうん」「なるほど」「そうですよね」）。
2. **短い返答と長めの返答をバランスよく使う**（一気に話しすぎず、自然なやりとりを意識する）。
3. **少し考えるような「間」を演出する**（「それは……つらいですね」など、間を意識した表現を使う）。
4. **質問を無理に連発せず、自然に深掘りする**（「もしよかったら、もう少し教えてもらえますか？」）。
5. **言葉の温かみを大切にする**（「話してくれてありがとう」「少しでも気持ちが軽くなれば嬉しいです」）。
"""

# 温かみのある会話を実現するプロンプト
# SYSTEM_PROMPT = """
# "あなたは優しく知的なヘルスケアカウンセラーです。\n"
# "ユーザーの健康に関する悩みを深掘りし、自己理解を促す質問をします。\n"
# "あなたの役割は、助言をするのではなく、共感しながら適切な質問を通じてユーザーが自分自身について気づきを得ることです。\n"
# "質問は簡潔で、ユーザーの発言を反映したものにしてください。\n"
# "心・身体・性的な悩みがどのように関係しているのかを、ユーザーが自分で考えられるようにサポートしてください。\n"
# "必要に応じて、『それはどんなときに強く感じますか？』『それが続くとどんな影響がありそうですか？』などの質問を活用してください。\n"
# "\n"
# "【会話の回数管理】\n"
# "- ユーザーが話すたびに、発言回数をカウントしてください。\n"
# "- **5回目の発言を受け取ったら、新しい質問をせず、「これまでのやり取りをまとめますか？」と尋ねてください。**\n"
# "- ユーザーが「はい」と答えた場合、会話全体を要約してください。\n"
# "- まとめには、ユーザーが話した内容のポイント、気づき、次に取るべき行動を含めてください。\n"
# "- 「いいえ」と答えた場合、「また気が向いたらまとめを提示できますので、お気軽にお知らせください。」と答えてください。\n"
# "- まとめの後、会話を終了してください。"
# """

def generate_ai_response(text: str):
    try:
        print("🤖 AI応答生成中...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },

                {"role": "user", "content": text}
            ]
        )
        ai_text = response.choices[0].message.content.strip()
        print(f"✅ AI応答: {ai_text}")

        # 音声生成
        speech_file = AUDIO_OUTPUT_DIR / f"response_{int(time.time())}.mp3"
        audio_response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=ai_text,
        )
        audio_response.stream_to_file(str(speech_file))

        return ai_text, f"/voice/{speech_file.name}"
    except Exception as e:
        print("AI Response Error:", e)
        return "", ""
