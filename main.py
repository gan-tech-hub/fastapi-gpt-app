from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict
from fastapi import File, UploadFile
import PyPDF2
from io import BytesIO

# .env 読み込み
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAIクライアント初期化
client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番ではNext.js URLなどに制限推奨
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    history: List[Dict[str, str]]
    mode: str

# 動作確認用
@app.get("/")
async def root():
    return {"message": "FastAPI with OpenAI is working!"}

# GPTチャットエンドポイント
@app.post("/chat")
async def chat(request: ChatRequest):
    message = request.history
    mode = request.mode  # + mode取り出し

    if not message:
        return {"response": "メッセージが送信されていません。"}

    # チャットボットモード
    if mode == "chat":
        # GPT呼び出し
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=message
        )
        ai_message = completion.choices[0].message.content

    # テキスト要約モード
    elif mode == "text-summary":
        # 要約用Systemメッセージ付与
        summary_messages = [
            {"role": "system", "content": "あなたは優秀な要約アシスタントです。ユーザーのテキストを簡潔に要約してください。"},
            *message
        ]
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=summary_messages
        )
        ai_message = completion.choices[0].message.content

    # PDF要約モード
    elif mode == "pdf-summary":
        ai_message = "PDF要約モードが選択されています（要約処理未実装）"

    # エラー処理
    else:
        ai_message = "不明なモードです"

    return {"response": ai_message}

# PDF要約エンドポイント
@app.post("/pdf-summary")
async def pdf_summary(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        reader = PyPDF2.PdfReader(BytesIO(contents))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        if not text.strip():
            return {"summary": "PDFからテキストを抽出できませんでした。"}

        # GPTへ要約依頼
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "以下のテキストを日本語で要約してください。"},
                {"role": "user", "content": text}
            ]
        )
        summary = completion.choices[0].message.content
        return {"response": summary}

    except Exception as e:
        print(e)
        return {"response": "PDF要約中にエラーが発生しました。"}
