import asyncio
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, query
import inspect

async def explore_client_attributes():
    """ClaudeSDKClientの属性とメソッドを調べる"""
    async with ClaudeSDKClient() as client:
        print("=== ClaudeSDKClient の属性・メソッド調査 ===")
        
        # 全ての属性を取得
        all_attributes = dir(client)
        
        print("\n【全属性・メソッド一覧】")
        for attr in sorted(all_attributes):
            if not attr.startswith('_'):  # プライベート属性以外
                try:
                    value = getattr(client, attr)
                    attr_type = type(value).__name__
                    print(f"  {attr}: {attr_type}")
                except:
                    print(f"  {attr}: <取得不可>")
        
        print("\n【セッション関連っぽい属性】")
        session_related = [attr for attr in all_attributes 
                          if 'session' in attr.lower() or 'id' in attr.lower()]
        for attr in session_related:
            try:
                value = getattr(client, attr)
                print(f"  {attr}: {value} ({type(value).__name__})")
            except Exception as e:
                print(f"  {attr}: エラー - {e}")
        
        print("\n【プライベート属性も含めてセッション関連を探す】")
        private_session = [attr for attr in all_attributes 
                          if 'session' in attr.lower()]
        for attr in private_session:
            try:
                value = getattr(client, attr)
                print(f"  {attr}: {value}")
            except Exception as e:
                print(f"  {attr}: エラー - {e}")

async def try_different_approaches():
    """様々な方法でセッションIDを取得してみる"""
    async with ClaudeSDKClient() as client:
        print("\n=== セッションID取得の試行 ===")
        
        # アプローチ1: __dict__ を確認
        print("\n【アプローチ1: client.__dict__】")
        if hasattr(client, '__dict__'):
            for key, value in client.__dict__.items():
                print(f"  {key}: {value}")
        
        # アプローチ2: query実行後に属性変化を確認
        print("\n【アプローチ2: query実行前後の属性変化】")
        before_attrs = set(dir(client))
        
        await client.query("Hello")
        
        after_attrs = set(dir(client))
        new_attrs = after_attrs - before_attrs
        
        if new_attrs:
            print("  新しく追加された属性:")
            for attr in new_attrs:
                try:
                    value = getattr(client, attr)
                    print(f"    {attr}: {value}")
                except:
                    print(f"    {attr}: <取得不可>")
        else:
            print("  新しい属性は追加されませんでした")
        
        # アプローチ3: レスポンスオブジェクトを調べる
        print("\n【アプローチ3: レスポンスオブジェクトの調査】")
        async for message in client.receive_response():
            print(f"  メッセージタイプ: {type(message).__name__}")
            print(f"  メッセージ属性: {dir(message)}")
            
            # セッション関連属性を探す
            session_attrs = [attr for attr in dir(message) 
                           if 'session' in attr.lower() or 'id' in attr.lower()]
            if session_attrs:
                print("  セッション関連属性:")
                for attr in session_attrs:
                    try:
                        value = getattr(message, attr)
                        print(f"    {attr}: {value}")
                    except:
                        print(f"    {attr}: <取得不可>")
            break  # 最初のメッセージだけ確認

if __name__ == "__main__":
    asyncio.run(explore_client_attributes())
    print("\n" + "="*50 + "\n")
    asyncio.run(try_different_approaches())