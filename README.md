# AI Chat & PDF Summary API

FastAPI と OpenAI API を利用した、チャット・テキスト要約・PDF要約アプリのバックエンドです。

PDF要約では、PDFから抽出したテキストを一度にLLMへ送信せず、チャンク分割、部分要約、統合要約の流れで処理します。大容量PDFによるメモリ消費やOpenAI API呼び出し回数の増加を防ぐため、ファイルサイズ・抽出文字数・チャンク数にも上限を設けています。

また、APIレスポンスは `success / data / error` 形式に統一し、処理時間、PDFサイズ、抽出文字数、チャンク数、OpenAI API呼び出し回数などを `data.meta` として返します。フロントエンドではこのメタ情報を使い、AI処理の裏側を可視化できます。

## 主な機能

- ChatGPT風のチャットAPI
- テキスト要約API
- PDFアップロード要約API
- PDFテキストのチャンク分割
- チャンクごとの部分要約
- 部分要約をまとめる統合要約
- PDFファイルサイズ・抽出文字数・チャンク数の安全ガード
- OpenAI API呼び出しタイムアウト
- `success / data / error` 形式の統一APIレスポンス
- `data.meta` による処理メタ情報の返却
- Frontendからの起動状態確認用Health Check API
- Swagger UIによるAPI確認

## 使用技術

- Python 3.11+
- FastAPI
- Uvicorn
- OpenAI Python SDK
- PyPDF2
- python-dotenv
- python-multipart

## システム構成

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

## ディレクトリ構成

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

## 各ファイルの責務

| File | Responsibility |
| --- | --- |
| `main.py` | FastAPIルーティング、入力バリデーション、PDF読み込み、PDFテキスト抽出、レスポンス組み立て |
| `services/openai_service.py` | OpenAI API呼び出し、チャット応答、テキスト要約、PDF部分要約、PDF統合要約 |
| `services/text_chunker.py` | PDFから抽出した長文テキストのチャンク分割 |
| `services/api_response.py` | 成功レスポンス・エラーレスポンスの標準化 |

## PDF要約処理の流れ

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
API Response with metadata
```

短いPDFは1回の要約で処理し、長いPDFはチャンクごとに部分要約してから統合要約します。

## 安全ガード

| Guard | Value | Purpose |
| --- | ---: | --- |
| PDF file size | 10MB | 大容量PDFによるメモリ消費を防ぐ |
| Extracted text length | 60,000 characters | 長すぎる入力で処理が重くなることを防ぐ |
| Chunk size | 3,500 characters | LLMに渡す単位を安定させる |
| Chunk overlap | 300 characters | チャンク境界で文脈が途切れることを軽減する |
| Max chunks | 20 | OpenAI API呼び出し回数の増加を防ぐ |
| OpenAI timeout | 60 seconds | API応答待ちで処理が止まり続けることを防ぐ |

PDF要約時のOpenAI API呼び出し回数は、最大で `部分要約20回 + 統合要約1回` の合計21回程度に制御されます。

## APIエンドポイント

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/` | Backendの疎通確認 |
| GET | `/health` | Frontendからの起動状態確認 |
| POST | `/chat` | チャット・テキスト要約 |
| POST | `/pdf-summary` | PDFアップロード要約 |

Swagger UI:

```text
http://localhost:8000/docs
```

## Health Check

Frontendは初期表示時に `GET /health` を呼び出し、Backendが利用可能か確認します。

Renderなど、一定時間アクセスがないとスリープする環境では、このリクエストがBackendの起動トリガーにもなります。

レスポンス:

```json
{
  "success": true,
  "data": {
    "status": "ok"
  },
  "error": null
}
```

`/health` ではOpenAI APIへの接続確認やPDF処理は行いません。Backendプロセスが起動し、HTTPリクエストを受けられる状態であることだけを軽量に返します。

## APIレスポンス形式

成功時:

```json
{
  "success": true,
  "data": {
    "message": "要約またはチャット応答本文",
    "meta": {
      "mode": "pdf",
      "elapsed_ms": 1234,
      "file_size_bytes": 102400,
      "extracted_text_chars": 15000,
      "chunk_count": 5,
      "max_chunks": 20,
      "chunk_size": 3500,
      "chunk_overlap": 300,
      "openai_call_count": 6
    }
  },
  "error": null
}
```

`data.meta` は処理内容に応じて返却されます。チャット・テキスト要約では `mode` と `elapsed_ms`、PDF要約ではPDFサイズやチャンク数などの詳細情報も返します。

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

## 代表的なエラーコード

| Code | Description |
| --- | --- |
| `EMPTY_MESSAGE` | チャットメッセージが空 |
| `UNKNOWN_MODE` | 未定義のモードが指定された |
| `PDF_FILE_TOO_LARGE` | PDFファイルサイズが上限を超過 |
| `PDF_TEXT_TOO_LONG` | PDFから抽出されたテキスト量が上限を超過 |
| `PDF_TEXT_NOT_FOUND` | PDFからテキストを抽出できない |
| `OPENAI_API_ERROR` | OpenAI API呼び出しに失敗 |
| `PDF_SUMMARY_FAILED` | PDF要約処理で想定外エラーが発生 |

## 環境変数

`.env`

```env
OPENAI_API_KEY=your-openai-api-key
```

## ローカル起動手順

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
http://localhost:8000/health
http://localhost:8000/docs
```

## Frontend連携

フロントエンドは `chat-summary-app` に配置されています。

ローカル連携時は、Frontend側の `.env.local` に以下を設定します。

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 動作確認項目

- `GET /` で疎通確認できること
- `GET /health` で `success: true` と `data.status: ok` が返ること
- `POST /chat` のチャットモードで回答が返ること
- `POST /chat` の要約モードで要約が返ること
- `POST /pdf-summary` で短いPDFを要約できること
- 長いPDFでチャンク分割、部分要約、統合要約が行われること
- 10MBを超えるPDFで分かりやすいエラーが返ること
- APIレスポンスが `success / data / error` 形式で統一されていること
- 成功時に `data.meta.elapsed_ms` などの処理メタ情報が返ること
- OpenAI APIキー未設定時に起動またはAPI呼び出しで問題を検知できること

## ポートフォリオでのアピールポイント

- FastAPIのルーティング層とOpenAI連携処理をサービス層に分離
- 長文PDFに対して、チャンク分割、部分要約、統合要約のLLM処理パイプラインを実装
- 大容量PDFでアプリが応答不能になる問題に対して、サイズ・文字数・チャンク数のガードを実装
- APIレスポンスを `success / data / error` 形式に統一し、フロントエンドとの連携を整理
- Renderのスリープ復帰を想定し、Frontendから軽量に確認できる `/health` を提供
- `data.meta` により、処理時間、チャンク数、API呼び出し回数などを可視化
- OpenAI APIキーをバックエンドでのみ扱う構成にし、フロントエンドへ公開しない設計
- エラーコードとメッセージを整理し、ユーザーに分かりやすいエラー表示へつなげられる構成

## 今後の改善予定

- Pydanticによるリクエスト・レスポンススキーマ定義
- PDFページ数、抽出文字数、チャンク数、処理時間のより詳細なログ出力
- PDF内容に対する質問応答機能
- 要約スタイル選択
- CORSの本番URL制限
- pytestによるAPIテスト追加
- `/health` の自動テスト追加
- CIによる依存インストール・構文チェック・テスト自動化
- Render / Railway などへのバックエンドデプロイ手順整理
