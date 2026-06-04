# AI Chat & PDF Summary API

FastAPI と OpenAI API を利用した、チャット・テキスト要約・PDF要約アプリのバックエンドです。

PDF要約では、PDFから抽出したテキストを一度にLLMへ送信せず、チャンク分割、部分要約、統合要約の流れで処理します。大容量PDFによるメモリ消費やOpenAI API呼び出し回数の増加を防ぐため、ファイルサイズ・抽出文字数・チャンク数にも上限を設けています。

## Features

- ChatGPT風のチャットAPI
- テキスト要約API
- PDFアップロード要約API
- PDFテキストのチャンク分割
- チャンクごとの部分要約
- 部分要約をまとめる統合要約
- PDFファイルサイズ・抽出文字数・チャンク数の安全ガード
- OpenAI API呼び出しタイムアウト
- `success / data / error` 形式の統一APIレスポンス
- Swagger UIによるAPI確認

## Tech Stack

- Python 3.11+
- FastAPI
- Uvicorn
- OpenAI Python SDK
- PyPDF2
- python-dotenv
- python-multipart
- Pydantic

## Architecture

```text
Next.js Frontend
      |
      | fetch
      v
FastAPI Backend
      |
      | OpenAI SDK
      v
OpenAI API
```

OpenAI APIキーはバックエンド側でのみ管理し、フロントエンドには公開しません。

## PDF Summary Flow

```text
PDF Upload
   |
   v
File Size Check
   |
   v
Text Extraction with PyPDF2
   |
   v
Extracted Text Size Check
   |
   v
Chunk Split
   |
   v
Partial Summaries
   |
   v
Integrated Summary
   |
   v
API Response
```

## Safety Guards

| Guard | Value | Purpose |
| --- | ---: | --- |
| PDF file size | 10MB | 大容量PDFによるメモリ消費を防ぐ |
| Extracted text length | 60,000 characters | 長すぎる入力で処理が重くなるのを防ぐ |
| Chunk size | 3,500 characters | LLMに渡す単位を安定させる |
| Chunk overlap | 300 characters | 文脈の途切れを軽減する |
| Max chunks | 20 | OpenAI API呼び出し回数の増加を防ぐ |
| OpenAI timeout | 60 seconds | API応答待ちで処理が止まり続けるのを防ぐ |

最大チャンク数が20のため、PDF要約時のOpenAI API呼び出しは最大で「部分要約20回 + 統合要約1回」の合計21回程度に制御されます。

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/` | Backendの疎通確認 |
| POST | `/chat` | チャット・テキスト要約 |
| POST | `/pdf-summary` | PDFアップロード要約 |

Swagger UI:

```text
http://localhost:8000/docs
```

## API Response Format

成功時:

```json
{
  "success": true,
  "data": {
    "message": "要約またはチャット応答本文"
  },
  "error": null
}
```

エラー時:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "PDF_FILE_TOO_LARGE",
    "message": "PDFファイルサイズが大きすぎます。10MB以下のPDFをアップロードしてください。"
  }
}
```

## Error Codes

| Code | Description |
| --- | --- |
| `EMPTY_MESSAGE` | チャットメッセージが空 |
| `UNKNOWN_MODE` | 未定義のモードが指定された |
| `PDF_FILE_TOO_LARGE` | PDFファイルサイズが上限を超過 |
| `PDF_TEXT_TOO_LONG` | PDFから抽出されたテキスト量が上限を超過 |
| `PDF_TEXT_NOT_FOUND` | PDFからテキストを抽出できない |
| `OPENAI_API_ERROR` | OpenAI API呼び出しに失敗 |
| `PDF_SUMMARY_FAILED` | PDF要約処理で想定外エラーが発生 |

## Directory Structure

```text
fastapi-gpt-app/
├── main.py
├── requirements.txt
├── services/
│   ├── __init__.py
│   ├── api_response.py
│   ├── openai_service.py
│   └── text_chunker.py
└── README.md
```

## Main Modules

| File | Responsibility |
| --- | --- |
| `main.py` | FastAPIルーティング、PDF読み込み、PDFテキスト抽出、入力ガード |
| `services/openai_service.py` | OpenAI API呼び出し、チャット、テキスト要約、PDF部分要約、統合要約 |
| `services/text_chunker.py` | PDF抽出テキストのチャンク分割 |
| `services/api_response.py` | 成功・エラーレスポンスの標準化 |

## Environment Variables

`.env`

```env
OPENAI_API_KEY=your-openai-api-key
```

## Local Setup

Windows PowerShellでの起動例です。

```powershell
cd C:\dev\GItHub\fastapi_app\fastapi-gpt-app
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Set-Content -Path .env -Value "OPENAI_API_KEY=your-openai-api-key" -Encoding ascii
uvicorn main:app --reload
```

起動後:

```text
http://localhost:8000
http://localhost:8000/docs
```

## Frontend

フロントエンドは `chat-summary-app` に分離しています。

ローカル連携時は、Frontend側の `.env.local` に以下を設定します。

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Portfolio Highlights

- FastAPIのルーティング層とOpenAI連携処理をサービス層に分離
- 長文PDFに対して、チャンク分割、部分要約、統合要約のLLM処理パイプラインを実装
- 大容量PDFでアプリが応答不能になる問題に対して、サイズ・文字数・チャンク数のガードを実装
- APIレスポンスを `success / data / error` 形式に統一
- OpenAI APIキーをバックエンドでのみ扱う構成にし、フロントエンドへ公開しない設計

## Future Improvements

- PDF内容への質問機能
- 要約スタイル選択
- PDFページ数、抽出文字数、チャンク数、処理時間の表示
- Pydanticによるレスポンススキーマ定義
- CORSの本番URL制限
- CIによる依存インストール・構文チェックの自動化
- Render / Vercel への再デプロイ手順整理
