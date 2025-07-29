# 📦 FastAPI GPT App

FastAPI + OpenAI API を活用したチャット＆PDF要約APIサーバーです。  
フロントエンド（Next.js）は別リポジトリで構成しています。

---

## 🚀 アプリ概要

| 項目 | 内容 |
|------|------|
| バックエンド | FastAPI |
| 機能 | - チャットAPI<br>- PDF要約API |
| 外部API | OpenAI API |
| フロントエンド | [next-fastapi-gpt（Vercel）](https://chat-summary-app.vercel.app) |
| APIドキュメント | [Swagger UI](https://chat-summary-backend.onrender.com/docs) |

---

## 🧩 使用技術

- Python 3.11+
- FastAPI
- Uvicorn
- OpenAI Python SDK
- PyMuPDF（PDF解析用）

---

## 🔧 セットアップ手順（ローカル）

```bash
# 仮想環境の作成・有効化
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt

# .env ファイルの作成（OpenAI APIキーなど）
echo "OPENAI_API_KEY=your-api-key" > .env

# サーバー起動
uvicorn main:app --reload
```

---

## 🌐 APIエンドポイント

| メソッド | エンドポイント        | 説明                   |
| ---- | -------------- | -------------------- |
| POST | `/chat`        | ChatGPT API による応答を返す |
| POST | `/pdf-summary` | アップロードした PDF の要約を生成  |

※ 詳細は `/docs` を参照。

---

## 📡 デプロイ情報

| 環境           | サービス   | URL                                                                                    |
| ------------- | ------ | -------------------------------------------------------------------------------------- |
| Backend (API) | Render | [https://chat-summary-backend.onrender.com](https://chat-summary-backend.onrender.com) |
| Frontend      | Vercel | [https://chat-summary-app.vercel.app](https://chat-summary-app.vercel.app)             |

---

## 🔐 環境変数（`.env`）

| 変数名              | 説明           |
| ---------------- | ------------ |
| `OPENAI_API_KEY` | OpenAIのAPIキー |

---

## 🗂 ディレクトリ構成

```bash
fastapi-gpt-app/
├── .gitignore
├── main.py
├── requirements.txt
├── .env
```

---

## 👤 作者

* 桜庭祐斗

---

## 📝 補足

* フロントエンドとの連携が必要です。Next.js側のリポジトリに環境変数 `NEXT_PUBLIC_API_URL` を設定してください。
* フロント実装の詳細は別リポジトリをご参照ください。

```
