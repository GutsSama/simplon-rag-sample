import argparse
import asyncio
import httpx
import uuid
import time
import random

MESSAGES = [
    "Qu'est-ce que le RAG ?",
    "Comment fonctionne Mistral AI ?",
    "Explique moi l'observabilité LLM.",
    "Combien de requêtes peut-on traiter par seconde ?",
    "Où trouver la documentation Langfuse ?"
]

async def chat_scenario(client, base_url, message):
    try:
        # Create conversation
        response = await client.post(f"{base_url}/api/v1/conversations")
        response.raise_for_status()
        conversation_id = response.json()["conversation_id"]
        
        # Send message
        start = time.perf_counter()
        res = await client.post(
            f"{base_url}/api/v1/conversations/{conversation_id}/messages",
            json={"content": message}
        )
        res.raise_for_status()
        duration = time.perf_counter() - start
        
        print(f"✅ Success - Msg: '{message[:20]}...' | Latency: {duration:.2f}s")
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    parser = argparse.ArgumentParser(description="Bench traffic generator for RAG API")
    parser.add_argument("--url", default="http://localhost:8000", help="API Base URL")
    parser.add_argument("--messages", type=int, default=10, help="Number of messages to send")
    parser.add_argument("--concurrency", type=int, default=2, help="Max concurrent requests")
    args = parser.parse_args()

    print(f"Starting benchmark: {args.messages} requests to {args.url} (max {args.concurrency} concurrent)")
    
    semaphore = asyncio.Semaphore(args.concurrency)
    
    async def bounded_chat(client, url, msg):
        async with semaphore:
            await chat_scenario(client, url, msg)
            
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = []
        for _ in range(args.messages):
            msg = random.choice(MESSAGES)
            tasks.append(bounded_chat(client, args.url, msg))
            
        await asyncio.gather(*tasks)
        
    print("Benchmark complete.")

if __name__ == "__main__":
    asyncio.run(main())
