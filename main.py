from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict
import PyPDF2
import time
from io import BytesIO

from services.api_response import error_response, success_response
from services.openai_service import (
    MAX_PDF_CHUNKS,
    OpenAIServiceError,
    PDF_CHUNK_OVERLAP,
    PDF_CHUNK_SIZE,
    generate_chat_response,
    generate_pdf_summary,
    generate_text_summary,
)

MAX_PDF_FILE_SIZE_BYTES = 10 * 1024 * 1024
MAX_EXTRACTED_TEXT_CHARS = 60_000
UPLOAD_READ_CHUNK_SIZE_BYTES = 1024 * 1024

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


class PDFProcessingError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


async def read_pdf_file_with_limit(file: UploadFile) -> bytes:
    chunks = []
    total_size = 0

    while True:
        chunk = await file.read(UPLOAD_READ_CHUNK_SIZE_BYTES)
        if not chunk:
            break

        total_size += len(chunk)
        if total_size > MAX_PDF_FILE_SIZE_BYTES:
            raise PDFProcessingError(
                code="PDF_FILE_TOO_LARGE",
                message="PDFファイルサイズが大きすぎます。10MB以下のPDFをアップロードしてください。",
                status_code=413,
            )

        chunks.append(chunk)

    return b"".join(chunks)


def extract_pdf_text_with_limit(contents: bytes) -> str:
    reader = PyPDF2.PdfReader(BytesIO(contents))
    page_texts = []
    total_text_length = 0

    for page in reader.pages:
        page_text = page.extract_text() or ""
        total_text_length += len(page_text)
        if total_text_length > MAX_EXTRACTED_TEXT_CHARS:
            raise PDFProcessingError(
                code="PDF_TEXT_TOO_LONG",
                message="PDFから抽出されたテキストが多すぎます。短いPDF、または範囲を絞ったPDFでお試しください。",
            )
        page_texts.append(page_text)

    return "".join(page_texts)

# 動作確認用
@app.get("/")
async def root():
    return success_response("FastAPI with OpenAI is working!")


@app.get("/health")
async def health():
    return JSONResponse(
        content={
            "success": True,
            "data": {
                "status": "ok",
            },
            "error": None,
        },
    )

# GPTチャットエンドポイント
@app.post("/chat")
async def chat(request: ChatRequest):
    start_time = time.perf_counter()
    message = request.history
    mode = request.mode  # + mode取り出し

    if not message:
        return error_response("EMPTY_MESSAGE", "メッセージが送信されていません。")

    # チャットボットモード
    try:
        if mode == "chat":
            ai_message = generate_chat_response(message)

        # テキスト要約モード
        elif mode == "text-summary":
            ai_message = generate_text_summary(message)

        # PDF要約モード
        elif mode == "pdf-summary":
            ai_message = "PDF要約モードが選択されています（要約処理未実装）"

        # エラー処理
        else:
            return error_response("UNKNOWN_MODE", "不明なモードです。")
    except OpenAIServiceError as e:
        print(e)
        return error_response("OPENAI_API_ERROR", str(e), status_code=502)

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)
    return success_response(
        ai_message,
        meta={
            "mode": mode,
            "elapsed_ms": elapsed_ms,
        },
    )

# PDF要約エンドポイント
@app.post("/pdf-summary")
async def pdf_summary(file: UploadFile = File(...)):
    start_time = time.perf_counter()
    try:
        contents = await read_pdf_file_with_limit(file)
        text = extract_pdf_text_with_limit(contents)
        if not text.strip():
            return error_response("PDF_TEXT_NOT_FOUND", "PDFからテキストを抽出できませんでした。")

        result = generate_pdf_summary(text)
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return success_response(
            result.summary,
            meta={
                "mode": "pdf-summary",
                "elapsed_ms": elapsed_ms,
                "file_size_bytes": len(contents),
                "extracted_text_chars": len(text),
                "chunk_count": result.chunk_count,
                "max_chunks": MAX_PDF_CHUNKS,
                "chunk_size": PDF_CHUNK_SIZE,
                "chunk_overlap": PDF_CHUNK_OVERLAP,
                "openai_call_count": result.openai_call_count,
            },
        )

    except PDFProcessingError as e:
        print(e)
        return error_response(e.code, e.message, status_code=e.status_code)
    except OpenAIServiceError as e:
        print(e)
        return error_response("OPENAI_API_ERROR", str(e), status_code=502)
    except Exception as e:
        print(e)
        return error_response("PDF_SUMMARY_FAILED", "PDF要約中にエラーが発生しました。", status_code=500)
