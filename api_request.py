from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from claude_code_sdk import query, ClaudeCodeOptions
import uuid
from typing import Optional

# データモデル定義
# FastAPIが：
# 1.HTTPボディからJSONを読み取り
# 2.ChatQueryオブジェクトに変換
# 3.関数の引数query_dataとして渡す
class ChatQuery(BaseModel):
    query: str
    request_id: Optional[str] = None # 個別のリクエストを追跡するため
    resume_session: Optional[str] = None  # セッションを再開するためのclaude codeが生成したid

# ヘルスチェックAPI
# curl http://localhost:8002/health
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# メインチャットAPI
# curl -X POST "http://localhost:8002/api/chat" \
#      -H "Content-Type: application/json" \
#      -d '{"query": "私の名前を覚えていますか？", "resume_session": "前のsession_id"}'
@app.post("/api/chat") # このデコレータでルーティング登録し、受け付けられるようにする
async def chat_with_ai(query_data: ChatQuery): # asyncで非同期処理なので、レスが早く平行処理も可能

    # 準備
    request_id = query_data.request_id or str(uuid.uuid4()) # request_idの生成
    if not query_data.query.strip(): # queryが空なら、400を返す
        raise HTTPException(status_code=400, detail="質問が空です")

    # 処理
    try:
        options = ClaudeCodeOptions(
            system_prompt="あなたは親切なAIアシスタントです。質問に丁寧に答えてください。",
            max_turns=10
        )

        if query_data.resume_session:
            # セッション継続の場合
            options.continue_conversation = True
            options.resume = query_data.resume_session
            print(f"セッション継続: {query_data.resume_session}")
        else:
            # 新規セッションの場合
            options.continue_conversation = False
            print("新しいセッションを開始")

        # Claude Code SDKのquery関数を使用
        messages = []
        session_id = None

        # ストリーミング形式である必要がないので、for文で回す必要ない変更必要かも
        # queryメソッドで、リクエストし、messageを受ける
        async for message in query(prompt=query_data.query, options=options):
            messages.append(message)
            print(f"受信メッセージ: {message}")

            # セッションIDを取得
            if hasattr(message, 'session_id') and message.session_id:
                session_id = message.session_id
                print(f"取得したセッションID: {session_id}")
            elif hasattr(message, 'data') and isinstance(message.data, dict):
                if 'session_id' in message.data:
                    session_id = message.data['session_id']
                    print(f"データからセッションID取得: {session_id}")

        # レスポンステキストを連結していく
        # messageの中にcontentが含まれるので、繋ぎ合わせていく
        response_text = ""
        for message in messages:
            if hasattr(message, 'content'):
                for block in message.content:
                    if hasattr(block, 'text'):
                        response_text += block.text

        # 既存セッション: セッション指定された場合、それを返す新規の場合は生成されたID
        # 新規セッション: session_idを返す
        final_session_id = query_data.resume_session if query_data.resume_session else session_id #最後に受信したメッセージのsession_idなので、不安定になってるかも

        return JSONResponse(content={
            "request_id": request_id,
            "session_id": final_session_id,  # 次回の会話継続用セッションID
            "query": query_data.query,
            "response": response_text,
            "is_continuation": bool(query_data.resume_session),  # 継続セッションかどうかを示す
            # "messages": [msg.dict() if hasattr(msg, 'dict') else str(msg) for msg in messages]  # デバッグ用
        })

    except Exception as e:
        print(f"エラー詳細: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI応答エラー: {str(e)}")

