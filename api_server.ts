import express from 'express';
import { createApiRouter } from './api_request';

const app = express();
app.use(express.json());

// APIルーターをマウント
app.use('/api', createApiRouter());

// ルートレベルのヘルスチェック（既存のAPIと互換性を保つため）
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// サーバー起動
function startServer() {
  const PORT = parseInt(process.env.PORT || '8003', 10);

  console.log('🚀 Claude Code SDK HTTP APIサーバーを起動します...\n');

  app.listen(PORT, '0.0.0.0', () => {
    console.log('✅ サーバーが起動しました！');
    console.log(`📱 http://localhost:${PORT}/api/chat にPOSTで質問を送信`);
    console.log(`🔄 会話継続機能付き（resume_session パラメータを使用）`);
    console.log(`💡 ヘルスチェック: http://localhost:${PORT}/health`);
    console.log('\n📝 curlコマンド例:');
    console.log('\n🆕 新規会話:');
    console.log(`curl -X POST http://localhost:${PORT}/api/chat \\`);
    console.log('  -H "Content-Type: application/json" \\');
    console.log('  -d \'{"query": "こんにちは！"}\'');
    console.log('\n🔄 会話継続（session_idを指定）:');
    console.log(`curl -X POST http://localhost:${PORT}/api/chat \\`);
    console.log('  -H "Content-Type: application/json" \\');
    console.log('  -d \'{"query": "続きを教えて", "resume_session": "取得したsession_id"}\'');
    console.log('');
  });
}

startServer();
