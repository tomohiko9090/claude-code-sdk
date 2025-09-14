import { query } from "@anthropic-ai/claude-code";

async function main() {
  console.log("クエリを開始します...");

  try {
    const abortController = new AbortController();

    // 30秒でタイムアウト
    const timeout = setTimeout(() => {
      console.log("タイムアウトしました。処理を中断します。");
      abortController.abort();
    }, 30000);

    let messageCount = 0;

    for await (const message of query({
      prompt: "lsコマンドを実行してください",
      options: {
        maxTurns: 5,
        appendSystemPrompt: "あなたはエンジニアです",
        allowedTools: ["Bash", "Read", "WebSearch"],
        abortController,
      }
    })) {
      messageCount++;
      console.log(`メッセージ ${messageCount} を受信:`, message.type);
      
      if (message.type === "result" && message.subtype === "success") {
        console.log("成功結果:", message.result);
      } else if (message.type === "error") {
        console.error("エラーメッセージ:", message);
      } else if (message.type === "assistant") {
        console.log("アシスタントメッセージ:", {
          id: message.message?.id,
          stop_reason: message.message?.stop_reason,
          content_length: message.message?.content?.length,
          uuid: message.uuid
        });
      } else {
        console.log("その他のメッセージ:", message.type, message.subtype || '');
      }
    }

    clearTimeout(timeout);
    console.log(`処理完了。合計 ${messageCount} 個のメッセージを受信しました。`);
    
  } catch (error) {
    console.error("エラーが発生しました:", error);
  }
}

main().catch(console.error);

