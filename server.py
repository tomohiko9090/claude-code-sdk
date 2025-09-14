# server.py
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

app = FastAPI(title="法務エージェント API", description="法務相談のためのAIアシスタント")

class LegalQuery(BaseModel):
    query: str
    max_turns: int = 2

class LegalAgent:
    def __init__(self):
        self.system_prompt = "あなたは法務アシスタントです。リスクを特定し、改善を提案してください。"
    
    async def process_query(self, query: str, max_turns: int = 2):
        """法務クエリを処理し、ストリーミングレスポンスを返す"""
        try:
            # モックレスポンス（claude-code-sdkの代わり）
            import asyncio
            
            # 法務分析のモックレスポンス
            mock_response = f"""
## 法務分析結果

**受信したクエリ**: {query}

### 🔍 リスク分析
1. **契約条項の確認**: 提供された内容について以下の点を検討しました
2. **法的リスク**: 潜在的な問題点を特定
3. **改善提案**: より安全な条項への修正案

### ⚖️ 法的観点
- **適用法**: 日本の民法・商法に基づく分析
- **判例**: 関連する裁判例の検討
- **実務**: 一般的な契約実務との比較

### 📋 推奨事項
1. 専門の弁護士による詳細レビューを推奨
2. 契約相手方との協議が必要
3. 定期的な契約条項の見直し

**注意**: これはデモンストレーション用のモックレスポンスです。
実際の法務相談には専門家にご相談ください。
            """
            
            # ストリーミング風にレスポンスを分割して送信
            words = mock_response.split()
            newline_char = '\n'
            for i, word in enumerate(words):
                await asyncio.sleep(0.05)  # 50ms間隔でストリーミング
                yield f"data: {json.dumps({'text': word + ' '}, ensure_ascii=False)}\n\n"
                
                # 10単語ごとに改行
                if (i + 1) % 10 == 0:
                    yield f"data: {json.dumps({'text': newline_char}, ensure_ascii=False)}\n\n"
            
            yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

# 法務エージェントのインスタンス
legal_agent = LegalAgent()

@app.get("/", response_class=HTMLResponse)
async def get_interface():
    """メインのWebインターフェースを返す"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>法務エージェント</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Hiragino Sans', 'Yu Gothic', 'Meiryo', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            
            .header {
                background: linear-gradient(135deg, #2c3e50, #34495e);
                color: white;
                padding: 30px;
                text-align: center;
            }
            
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
                font-weight: 300;
            }
            
            .header p {
                opacity: 0.9;
                font-size: 1.1em;
            }
            
            .content {
                padding: 30px;
            }
            
            .input-section {
                margin-bottom: 30px;
            }
            
            .input-group {
                margin-bottom: 20px;
            }
            
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #2c3e50;
            }
            
            textarea, input, select {
                width: 100%;
                padding: 15px;
                border: 2px solid #e0e6ed;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s ease;
            }
            
            textarea:focus, input:focus, select:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            textarea {
                resize: vertical;
                min-height: 120px;
                font-family: inherit;
            }
            
            .button-group {
                display: flex;
                gap: 15px;
                margin-top: 20px;
            }
            
            button {
                flex: 1;
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .btn-primary {
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
            }
            
            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }
            
            .btn-secondary {
                background: #f8f9fa;
                color: #6c757d;
                border: 2px solid #e9ecef;
            }
            
            .btn-secondary:hover {
                background: #e9ecef;
            }
            
            .response-section {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 25px;
                margin-top: 30px;
                min-height: 200px;
                border-left: 4px solid #667eea;
            }
            
            .response-title {
                font-size: 1.3em;
                font-weight: 600;
                color: #2c3e50;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .loading {
                display: none;
                color: #667eea;
            }
            
            .spinner {
                width: 20px;
                height: 20px;
                border: 2px solid #f3f3f3;
                border-top: 2px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            #response {
                white-space: pre-wrap;
                line-height: 1.6;
                color: #2c3e50;
                font-size: 15px;
            }
            
            .example-queries {
                background: #e8f4fd;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
            }
            
            .example-queries h3 {
                color: #2c3e50;
                margin-bottom: 15px;
            }
            
            .example-item {
                background: white;
                padding: 12px;
                margin: 8px 0;
                border-radius: 6px;
                cursor: pointer;
                transition: background-color 0.2s;
                border-left: 3px solid #667eea;
            }
            
            .example-item:hover {
                background: #f0f8ff;
            }
            
            .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 8px;
            }
            
            .status-ready { background-color: #28a745; }
            .status-processing { background-color: #ffc107; }
            .status-error { background-color: #dc3545; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚖️ 法務エージェント</h1>
                <p>AIによる法務リスク分析と改善提案</p>
            </div>
            
            <div class="content">
                <div class="example-queries">
                    <h3>📝 サンプルクエリ</h3>
                    <div class="example-item" onclick="setQuery('この契約条項の潜在的な問題を確認してください：「当事者は無制限の責任に同意する」')">
                        契約条項のリスク分析
                    </div>
                    <div class="example-item" onclick="setQuery('秘密保持契約書で注意すべき点を教えてください')">
                        NDAの注意点
                    </div>
                    <div class="example-item" onclick="setQuery('労働契約書の残業代条項について法的問題はありますか？')">
                        労働契約の確認
                    </div>
                </div>
                
                <div class="input-section">
                    <div class="input-group">
                        <label for="query">法務相談内容</label>
                        <textarea 
                            id="query" 
                            placeholder="契約書の条項、法的リスク、コンプライアンス事項などについてご質問ください..."
                        ></textarea>
                    </div>
                    
                    <div class="input-group">
                        <label for="maxTurns">最大ターン数</label>
                        <select id="maxTurns">
                            <option value="1">1ターン（簡潔な回答）</option>
                            <option value="2" selected>2ターン（標準）</option>
                            <option value="3">3ターン（詳細な分析）</option>
                        </select>
                    </div>
                    
                    <div class="button-group">
                        <button class="btn-primary" onclick="submitQuery()">
                            <span class="status-indicator status-ready"></span>
                            分析開始
                        </button>
                        <button class="btn-secondary" onclick="clearAll()">
                            クリア
                        </button>
                    </div>
                </div>
                
                <div class="response-section">
                    <div class="response-title">
                        🤖 AI法務アシスタントの回答
                        <div class="loading">
                            <div class="spinner"></div>
                        </div>
                    </div>
                    <div id="response">ここに分析結果が表示されます...</div>
                </div>
            </div>
        </div>
        
        <script>
            function setQuery(text) {
                document.getElementById('query').value = text;
            }
            
            function clearAll() {
                document.getElementById('query').value = '';
                document.getElementById('response').textContent = 'ここに分析結果が表示されます...';
                updateStatus('ready');
            }
            
            function updateStatus(status) {
                const indicator = document.querySelector('.status-indicator');
                indicator.className = `status-indicator status-${status}`;
                
                const loading = document.querySelector('.loading');
                if (status === 'processing') {
                    loading.style.display = 'flex';
                } else {
                    loading.style.display = 'none';
                }
            }
            
            async function submitQuery() {
                const query = document.getElementById('query').value.trim();
                const maxTurns = parseInt(document.getElementById('maxTurns').value);
                
                if (!query) {
                    alert('相談内容を入力してください。');
                    return;
                }
                
                updateStatus('processing');
                document.getElementById('response').textContent = '';
                
                try {
                    const response = await fetch('/api/legal-query', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            query: query,
                            max_turns: maxTurns
                        })
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    
                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        
                        const chunk = decoder.decode(value);
                        const lines = chunk.split('\\n');
                        
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                try {
                                    const data = JSON.parse(line.slice(6));
                                    
                                    if (data.error) {
                                        document.getElementById('response').textContent += `エラー: ${data.error}`;
                                        updateStatus('error');
                                    } else if (data.done) {
                                        updateStatus('ready');
                                    } else if (data.text) {
                                        document.getElementById('response').textContent += data.text;
                                    }
                                } catch (e) {
                                    console.error('JSON parse error:', e);
                                }
                            }
                        }
                    }
                } catch (error) {
                    console.error('Error:', error);
                    document.getElementById('response').textContent = `エラーが発生しました: ${error.message}`;
                    updateStatus('error');
                }
            }
            
            // Enterキーでの送信（Shift+Enterで改行）
            document.getElementById('query').addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    submitQuery();
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/legal-query")
async def legal_query_endpoint(query_data: LegalQuery):
    """法務クエリのAPIエンドポイント"""
    if not query_data.query.strip():
        raise HTTPException(status_code=400, detail="クエリが空です")
    
    # 簡単なJSONレスポンスでテスト
    return {
        "status": "success",
        "query": query_data.query,
        "max_turns": query_data.max_turns,
        "analysis": {
            "risks": ["無制限責任条項は高リスク", "契約解除条件が不明確", "損害賠償範囲が広すぎる"],
            "recommendations": ["責任限定条項の追加", "明確な解除条件の設定", "損害賠償額の上限設定"],
            "legal_basis": "民法第415条、第416条に基づく分析"
        },
        "note": "これはデモンストレーション用のモックレスポンスです。実際の法務相談には専門家にご相談ください。"
    }

@app.post("/api/legal-query-stream")
async def legal_query_stream_endpoint(query_data: LegalQuery):
    """法務クエリのストリーミングAPIエンドポイント"""
    if not query_data.query.strip():
        raise HTTPException(status_code=400, detail="クエリが空です")
    
    async def generate():
        async for chunk in legal_agent.process_query(query_data.query, query_data.max_turns):
            yield chunk
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy", "service": "legal-agent"}

@app.post("/api/test")
async def test_endpoint(query_data: LegalQuery):
    """テスト用のエンドポイント（claude-code-sdkを使わない）"""
    return {
        "status": "success",
        "received_query": query_data.query,
        "max_turns": query_data.max_turns,
        "message": "APIエンドポイントは正常に動作しています。claude-code-sdkの設定が必要です。"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 法務エージェントサーバーを起動中...")
    print("📱 ブラウザで http://localhost:8000 にアクセスしてください")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
