import { query, SDKMessage, SDKAssistantMessage, SDKSystemMessage } from '@anthropic-ai/claude-code';
import express from 'express';

// リクエスト用の型定義
export interface ChatRequest {
  query: string;
  request_id?: string;
  claude_uuid?: string;
  resume_session?: string;
}

// レスポンス用の型定義
export interface ChatResponse {
  request_id: string;
  session_id?: string;
  query: string;
  response: string;
  is_continuation: boolean;
}

// UUID生成関数
export function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

export function extractTextContent(message: SDKAssistantMessage): string | null {
  if (message.message?.content && Array.isArray(message.message.content)) {
    const textParts: string[] = [];
    for (const content of message.message.content) {
      if (content.type === 'text' && content.text) {
        textParts.push(content.text);
      }
    }
    return textParts.length > 0 ? textParts.join('\n') : null;
  }
  return null;
}

// APIルーターを作成してエクスポート
export function createApiRouter() {
  const router = express.Router();

  // チャットAPIエンドポイント
  router.post('/chat', async (req, res) => {
    try {
      const { query: userQuery, request_id, resume_session }: ChatRequest = req.body;

      // バリデーション
      if (!userQuery?.trim()) {
        return res.status(400).json({ error: '400エラーです' });
      }

      // リクエストIDの生成
      const requestId = request_id || generateUUID();

      console.log(`\n=== 新しいリクエスト ===`);
      console.log(`リクエストID: ${requestId}`);
      console.log(`質問: ${userQuery}`);
      console.log(`セッション継続: ${resume_session ? 'あり (' + resume_session + ')' : 'なし'}`);

      const messages: SDKMessage[] = [];
      let sessionId: string | undefined = undefined;

      // Claude Code SDKでクエリ実行
      const queryOptions: any = { maxTurns: 5 };
      console.log("セッション:",resume_session);

      if (resume_session) {
        queryOptions.resume = resume_session;
      }

      console.log("queryOptions:", queryOptions);

      for await (const message of query({
        prompt: userQuery,
        options: {maxTurns: 5, resume: resume_session}
      })) {
        messages.push(message);

        // セッションIDを取得
        if (message.type === 'system' && 'session_id' in message) {
          sessionId = (message as SDKSystemMessage & { session_id: string }).session_id;
          console.log(`📝 取得したセッションID: ${sessionId}`);
        }
      }

      // レスポンステキストを構築
      let responseText = '';
      for (const message of messages) {
        if (message.type === 'assistant') {
          const content = extractTextContent(message as SDKAssistantMessage);
          if (content) {
            responseText += content;
          }
        }
      }

      // セッションIDの決定ロジック
      let finalSessionId: string | undefined;
      let isContinuation = false;

      if (resume_session) {
        // セッション継続の場合：新しく生成されたセッションIDを使用
        finalSessionId = sessionId;  // ← ここを修正（resume_session → sessionId）
        isContinuation = true;
        console.log(`🔄 セッション継続: ${resume_session} → ${sessionId}`);
      } else {
        // 新規セッションの場合：新しく生成されたセッションIDを使用
        finalSessionId = sessionId;
        isContinuation = false;
        console.log(`🆕 新規セッション: ${sessionId}`);
      }

      const response: ChatResponse = {
        request_id: requestId,
        session_id: finalSessionId,
        query: userQuery,
        response: responseText,
        is_continuation: isContinuation
      };

      console.log(`✅ 応答完了 (${responseText.length}文字)`);
      console.log(`📝 返却セッションID: ${finalSessionId}`);
      
      res.json(response);

    } catch (error) {
      console.error('❌ エラー:', error);
      res.status(500).json({ 
        error: 'AI応答エラー',
        details: error instanceof Error ? error.message : String(error)
      });
    }
  });

  // ヘルスチェックエンドポイント
  router.get('/health', (req, res) => {
    res.json({ status: 'ok' });
  });

  return router;
}
