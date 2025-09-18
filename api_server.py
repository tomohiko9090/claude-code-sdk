import uvicorn

app = FastAPI(title="AI チャット API", description="Claude AIとのシンプルなチャット")

from api_request import *

if __name__ == "__main__":
    print("🤖 AIチャットサーバー起動中...")
    print("📱 http://localhost:8002/api/chat にPOSTで質問を送信")
    print("🔄 会話継続機能付き（resume_session パラメータを使用）")
    uvicorn.run("api_request:app", host="0.0.0.0", port=8002, reload=True)