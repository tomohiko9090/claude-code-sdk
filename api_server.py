# run_server.py - サーバー起動スクリプト
import uvicorn

if __name__ == "__main__":
    print("🤖 AIチャットサーバー起動中...")
    print("📱 http://localhost:8002/api/chat にPOSTで質問を送信")
    print("🔄 会話継続機能付き（resume_session パラメータを使用）")
    uvicorn.run("server2:app", host="0.0.0.0", port=8002, reload=True)