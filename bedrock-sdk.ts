// server.ts - TypeScript版AIチャットAPI
import 'dotenv/config';
import express from 'express';
import AnthropicBedrock from '@anthropic-ai/bedrock-sdk';
import { v4 as uuidv4 } from 'uuid';
import * as fs from 'fs/promises';
import * as path from 'path';

const app = express();
app.use(express.json());

// Claude Bedrock APIクライアントの初期化
const anthropic = new AnthropicBedrock({
  // AWS認証は環境変数から自動で取得される
  awsRegion: process.env.AWS_REGION || 'us-east-1',
});

// リクエストの型定義
interface ChatQuery {
  query: string;
  request_id?: string;  // オプションでリクエストUUIDを受け取る
  claude_uuid?: string;  // オプションでClaude UUIDを受け取る
  resume_session?: string;  // セッションを再開するためのsession_id
}

// レスポンスの型定義
interface ChatResponse {
  request_id: string;
  session_id: string | null;
  query: string;
  response: string;
  is_continuation: boolean;
}

// セッション管理用の型定義
interface MessageParam {
  role: 'user' | 'assistant';
  content: string;
}

interface SessionData {
  messages: MessageParam[];
  lastQuery: string;
  lastResponse: string;
  timestamp: Date;
}

// セッション管理用のマップ
const sessionMap = new Map<string, SessionData>();

app.post('/api/chat', async (req, res): Promise<void> => {
  try {
    const queryData: ChatQuery = req.body;
    
    // UUIDが指定されていない場合は自動生成
    const requestId = queryData.request_id || uuidv4();

    if (!queryData.query?.trim()) {
      res.status(400).json({ error: '質問が空です' });
      return;
    }

    console.log(`リクエスト受信: ${queryData.query}`);
    console.log(`セッション継続: ${queryData.resume_session || 'なし'}`);

    let sessionId: string | null = null;
    let messages: MessageParam[] = [];

    if (queryData.resume_session) {
      // セッション継続の場合
      sessionId = queryData.resume_session;
      const sessionData = sessionMap.get(sessionId);
      if (sessionData) {
        messages = [...sessionData.messages];
        console.log(`セッション継続: ${queryData.resume_session} (${messages.length}件のメッセージ)`);
      } else {
        console.log(`セッションが見つかりません: ${queryData.resume_session}`);
        // セッションが見つからない場合は新規セッションとして扱う
        sessionId = null;
      }
    }

    if (!sessionId) {
      // 新規セッションの場合
      sessionId = uuidv4();
      messages = [];
      console.log(`新しいセッション開始: ${sessionId}`);
    }

    // ユーザーメッセージを追加
    messages.push({
      role: 'user',
      content: queryData.query
    });

    try {
      // Claude Bedrock APIを呼び出し
      const model = process.env.ANTHROPIC_MODEL || 'us.anthropic.claude-sonnet-4-20250514-v1:0';
      const response = await anthropic.messages.create({
        model: model,
        max_tokens: 4000,
        system: 'あなたは親切なAIアシスタントです。質問に丁寧に答えてください。',
        messages: messages,
      });

      // レスポンステキストを抽出
      let responseText = '';
      if (response.content && response.content.length > 0) {
        for (const block of response.content) {
          if (block.type === 'text') {
            responseText += block.text;
          }
        }
      }

      // アシスタントメッセージを履歴に追加
      messages.push({
        role: 'assistant',
        content: responseText
      });

      // セッション情報を保存
      sessionMap.set(sessionId, {
        messages: messages,
        lastQuery: queryData.query,
        lastResponse: responseText,
        timestamp: new Date()
      });

      const chatResponse: ChatResponse = {
        request_id: requestId,
        session_id: sessionId,
        query: queryData.query,
        response: responseText,
        is_continuation: Boolean(queryData.resume_session)
      };

      console.log(`レスポンス送信: セッションID=${sessionId}`);
      res.json(chatResponse);

    } catch (apiError) {
      console.error('Claude API エラー:', apiError);
      throw apiError;
    }

  } catch (error) {
    console.error('エラー詳細:', error);
    res.status(500).json({ 
      error: `AI応答エラー: ${error instanceof Error ? error.message : String(error)}` 
    });
  }
});

// セッション一覧取得エンドポイント
app.get('/api/sessions', (req, res): void => {
  const sessions = Array.from(sessionMap.entries()).map(([id, data]) => ({
    session_id: id,
    last_query: data.lastQuery,
    timestamp: data.timestamp
  }));
  
  res.json({ sessions });
});

// 特定セッション情報取得エンドポイント
app.get('/api/sessions/:sessionId', (req, res): void => {
  const sessionId = req.params.sessionId;
  const sessionData = sessionMap.get(sessionId);
  
  if (!sessionData) {
    res.status(404).json({ error: 'セッションが見つかりません' });
    return;
  }
  
  res.json({
    session_id: sessionId,
    ...sessionData
  });
});

// セッション削除エンドポイント
app.delete('/api/sessions/:sessionId', (req, res): void => {
  const sessionId = req.params.sessionId;
  const deleted = sessionMap.delete(sessionId);
  
  if (!deleted) {
    res.status(404).json({ error: 'セッションが見つかりません' });
    return;
  }
  
  res.json({ message: 'セッションを削除しました', session_id: sessionId });
});

// カスタムコマンド実行用のエンドポイントを追加
app.post('/api/command', async (req, res): Promise<void> => {
  try {
    const { command, arguments: args } = req.body;
    
    // セッションIDを自動生成
    const sessionId = uuidv4();
    
    console.log(`カスタムコマンド実行: ${command} ${args || ''} (新セッション: ${sessionId})`);
    
    // コマンドファイル読み込み & 実行
    const commandPath = path.join('.claude', 'commands', `${command}.md`);
    let commandContent: string;
    
    try {
      commandContent = await fs.readFile(commandPath, 'utf-8');
      console.log(`コマンドファイル読み込み成功: ${commandPath}`);
    } catch (fileError) {
      console.error(`コマンドファイルが見つかりません: ${commandPath}`);
      res.status(404).json({ error: `コマンド '${command}' が見つかりません` });
      return;
    }
    
    // 引数を置換
    const processedCommand = commandContent.replace(/\$ARGUMENTS/g, args || '');
    
    // Claude APIを呼び出し（コマンドファイルの内容をシステムプロンプトに使用）
    const response = await anthropic.messages.create({
      model: process.env.ANTHROPIC_MODEL || 'anthropic.claude-3-5-sonnet-20241022-v2:0',
      max_tokens: 8000,
      system: processedCommand,
      messages: [{ role: 'user', content: `コマンド実行開始: ${command} ${args || ''}` }]
    });
    
    // レスポンステキストを抽出
    let responseText = '';
    if (response.content && response.content.length > 0) {
      for (const block of response.content) {
        if (block.type === 'text') {
          responseText += block.text;
        }
      }
    }

    // セッション情報を保存
    sessionMap.set(sessionId, {
      messages: [
        { role: 'user', content: `/${command} ${args || ''}` },
        { role: 'assistant', content: responseText }
      ],
      lastQuery: `/${command} ${args || ''}`,
      lastResponse: responseText,
      timestamp: new Date()
    });
    
    // レスポンスを返す（resume_sessionとして返す）
    res.json({
      command: command,
      result: responseText,
      resume_session: sessionId  // 次回の会話継続用
    });
    
  } catch (error) {
    console.error('コマンド実行エラー:', error);
    res.status(500).json({ 
      error: `コマンド実行エラー: ${error instanceof Error ? error.message : String(error)}` 
    });
  }
});

// ヘルスチェック
app.get('/health', (req, res): void => {
  res.json({ status: 'ok' });
});

// サーバー起動
const PORT = process.env.PORT || 8002;

if (require.main === module) {
  app.listen(PORT, () => {
    console.log('🤖 AIチャットサーバー起動中...');
    console.log(`📱 http://localhost:${PORT}/api/chat にPOSTで質問を送信`);
    console.log('🔄 会話継続機能付き（resume_session パラメータを使用）');
    console.log(`📋 セッション一覧: GET http://localhost:${PORT}/api/sessions`);
  });
}

export default app;
