# legal-agent.py
import asyncio
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

async def main():
    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt="あなたは法務アシスタントです。リスクを特定し、改善を提案してください。",
            max_turns=2
        )
    ) as client:
        # クエリを送信
        await client.query(
            "この契約条項の潜在的な問題を確認してください：'当事者は無制限の責任に同意する...'"
        )

        # レスポンスをストリーミング
        async for message in client.receive_response():
            if hasattr(message, 'content'):
                # 到着したストリーミングコンテンツを印刷
                for block in message.content:
                    if hasattr(block, 'text'):
                        print(block.text, end='', flush=True)

if __name__ == "__main__":
    asyncio.run(main())