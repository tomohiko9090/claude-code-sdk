import asyncio
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, query

async def start_new_session():
    async with ClaudeSDKClient() as client:
        # 最初のクエリを送信
        await client.query("Pythonでファイル読み込み機能を作ってください")

        print("セッションを開始しました")
        print("注意: 実際のセッションID取得方法はSDKドキュメントを確認してください")
        print(f"セッション管理用ID（仮）: session_{hash(str(client)) % 100000:05d}")

        # レスポンスを処理
        async for message in client.receive_response():
            if hasattr(message, 'content'):
                for block in message.content:
                    if hasattr(block, 'text'):
                        print(block.text, end='', flush=True)

# 方法2：セッション管理でquery関数を使用
async def resume_session():
    # 最新の会話を継続
    async for message in query(
        prompt="今度はパフォーマンス向上のためにこれをリファクタリングしてください",
        options=ClaudeCodeOptions(continue_conversation=True)
    ):
        if type(message).__name__ == "ResultMessage":
            print(message.result)

    # 特定のセッションを再開（実際のセッションIDが必要）
    # 注意: 以下のIDはサンプル用のダミーIDです
    # 実際の使用では、前回のセッションから取得した実際のIDを使用してください
    try:
        async for message in query(
            prompt="テストを更新してください",
            options=ClaudeCodeOptions(
                resume="550e8400-e29b-41d4-a716-446655440000",  # ダミーID
                max_turns=3
            )
        ):
            if type(message).__name__ == "ResultMessage":
                print(message.result)
    except Exception as e:
        print(f"セッション再開エラー: {e}")
        print("有効なセッションIDが必要です")

# 実行例を選択してください
if __name__ == "__main__":
    # 新しいセッションを開始
    asyncio.run(start_new_session())
    
    # または既存セッションを継続
    # asyncio.run(resume_session())