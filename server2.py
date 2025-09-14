# server2.py - シンプルなAIチャットAPI
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from claude_code_sdk import query, ClaudeCodeOptions
import uuid
from typing import Optional

app = FastAPI(title="AI チャット API", description="Claude AIとのシンプルなチャット")

class ChatQuery(BaseModel):
    query: str
    request_id: Optional[str] = None  # オプションでリクエストUUIDを受け取る
    claude_uuid: Optional[str] = None  # オプションでClaude UUIDを受け取る
    resume_session: Optional[str] = None  # セッションを再開するためのsession_id

@app.post("/api/chat")
async def chat_with_ai(query_data: ChatQuery):
    """Claude AIとチャット"""
    # UUIDが指定されていない場合は自動生成
    request_id = query_data.request_id or str(uuid.uuid4())

    if not query_data.query.strip():
        raise HTTPException(status_code=400, detail="質問が空です")

    try:
        # Claude Code SDKのオプション設定
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

        # レスポンステキストを構築
        response_text = ""
        for message in messages:
            if hasattr(message, 'content'):
                for block in message.content:
                    if hasattr(block, 'text'):
                        response_text += block.text

        # セッションIDの決定：継続セッションの場合は指定されたID、新規の場合は生成されたID
        final_session_id = query_data.resume_session if query_data.resume_session else session_id

        return JSONResponse(content={
            "request_id": request_id,
            "session_id": final_session_id,  # 次回の会話継続用セッションID
            "query": query_data.query,
            "response": response_text,
            "is_continuation": bool(query_data.resume_session),  # 継続セッションかどうかを示す
            "messages": [msg.dict() if hasattr(msg, 'dict') else str(msg) for msg in messages]  # デバッグ用
        })

    except Exception as e:
        print(f"エラー詳細: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI応答エラー: {str(e)}")

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    print("🤖 AIチャットサーバー起動中...")
    print("📱 http://localhost:8002/api/chat にPOSTで質問を送信")
    print("🔄 会話継続機能付き（resume_session パラメータを使用）")
    uvicorn.run("server2:app", host="0.0.0.0", port=8002, reload=True)


