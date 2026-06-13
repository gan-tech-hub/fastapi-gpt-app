from dataclasses import dataclass
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

from services.text_chunker import split_text_into_chunks


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-3.5-turbo"
PDF_CHUNK_SIZE = 3500
PDF_CHUNK_OVERLAP = 300
MAX_PDF_CHUNKS = 20
OPENAI_TIMEOUT_SECONDS = 60.0

client: Optional[OpenAI] = None


class OpenAIServiceError(Exception):
    pass


@dataclass
class PDFSummaryResult:
    summary: str
    chunk_count: int
    openai_call_count: int


def get_client() -> OpenAI:
    global client
    if client is None:
        if not OPENAI_API_KEY:
            raise OpenAIServiceError("OpenAI APIキーが設定されていません。.env の OPENAI_API_KEY を確認してください。")
        client = OpenAI(api_key=OPENAI_API_KEY, timeout=OPENAI_TIMEOUT_SECONDS)
    return client


def create_chat_completion(messages: List[Dict[str, str]]) -> str:
    try:
        completion = get_client().chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
        )
    except OpenAIError as exc:
        raise OpenAIServiceError("OpenAI API呼び出しに失敗しました。APIキー、利用上限、通信状況を確認してください。") from exc

    content = completion.choices[0].message.content
    if not content:
        raise OpenAIServiceError("OpenAI APIから空の応答が返されました。")

    return content


def generate_chat_response(messages: List[Dict[str, str]]) -> str:
    return create_chat_completion(messages)


def generate_text_summary(messages: List[Dict[str, str]]) -> str:
    summary_messages = [
        {
            "role": "system",
            "content": "あなたは優秀な要約アシスタントです。ユーザーのテキストを簡潔に要約してください。",
        },
        *messages,
    ]

    return create_chat_completion(summary_messages)


def generate_pdf_summary(text: str) -> PDFSummaryResult:
    chunks = split_text_into_chunks(
        text,
        chunk_size=PDF_CHUNK_SIZE,
        overlap=PDF_CHUNK_OVERLAP,
    )
    if not chunks:
        raise OpenAIServiceError("PDFから要約対象のテキストを取得できませんでした。")
    if len(chunks) > MAX_PDF_CHUNKS:
        raise OpenAIServiceError(
            f"PDFのテキスト量が多すぎます。要約対象は最大{MAX_PDF_CHUNKS}チャンクまでです。"
            "短いPDF、または範囲を絞ったPDFでお試しください。"
        )

    partial_summaries = [
        generate_partial_pdf_summary(chunk, index + 1, len(chunks))
        for index, chunk in enumerate(chunks)
    ]

    if len(partial_summaries) == 1:
        return PDFSummaryResult(
            summary=partial_summaries[0],
            chunk_count=len(chunks),
            openai_call_count=1,
        )

    integrated_summary = generate_integrated_pdf_summary(partial_summaries)
    return PDFSummaryResult(
        summary=integrated_summary,
        chunk_count=len(chunks),
        openai_call_count=len(chunks) + 1,
    )


def generate_partial_pdf_summary(chunk: str, index: int, total: int) -> str:
    return create_chat_completion(
        messages=[
            {
                "role": "system",
                "content": (
                    "あなたはPDF要約アシスタントです。"
                    "PDF本文の一部を読み、重要な主張、結論、数値、固有名詞を落とさずに日本語で要約してください。"
                    "この部分だけでは不明な内容は推測しないでください。"
                ),
            },
            {
                "role": "user",
                "content": f"これはPDF本文の {index}/{total} 番目のチャンクです。\n\n{chunk}",
            },
        ],
    )


def generate_integrated_pdf_summary(partial_summaries: List[str]) -> str:
    summaries_text = "\n\n".join(
        f"部分要約 {index + 1}:\n{summary}"
        for index, summary in enumerate(partial_summaries)
    )

    return create_chat_completion(
        messages=[
            {
                "role": "system",
                "content": (
                    "あなたはPDF要約アシスタントです。"
                    "複数の部分要約を統合し、PDF全体の要約として自然で読みやすい日本語にまとめてください。"
                    "重複は整理し、結論、重要ポイント、補足情報の順で構成してください。"
                ),
            },
            {"role": "user", "content": summaries_text},
        ],
    )
