import asyncio

import httpx

API_URL = "http://localhost:8000/api/v1"


async def populate():
    print("--- Waiting for API to be healthy ---")
    async with httpx.AsyncClient(timeout=10.0) as client:
        for _ in range(10):
            try:
                resp = await client.get(f"{API_URL}/health")
                if resp.status_code == 200:
                    print("API is healthy!")
                    break
            except Exception:
                pass
            print("Waiting for API...")
            await asyncio.sleep(2)
        else:
            print("API did not become healthy in time.")
            return

    print("\n--- Generating RAG Traffic ---")
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Create conversation
        resp = await client.post(f"{API_URL}/conversations")
        resp.raise_for_status()
        conv_id = resp.json()["conversation_id"]
        print(f"Created conversation: {conv_id}")

        # 2. Send messages
        messages = [
            "Bonjour, comment se passe l'admission chez Simplon ?",
            "Quelles sont les modalités d'évaluation ?",
            "Comment obtenir un financement ?",
            "Parle-moi de la vie des apprenants.",
            "C'est quoi le programme ?",
            "Merci, au revoir !",
        ]

        for msg in messages:
            print(f"Sending message: '{msg}'...")
            resp = await client.post(
                f"{API_URL}/conversations/{conv_id}/messages", json={"content": msg}
            )
            if resp.status_code == 200:
                print(f"OK: Response received ({len(resp.json()['content'])} chars)")
            else:
                print(f"ERROR: {resp.status_code} - {resp.text}")

    print("\n--- Traffic Generation Complete ---")


if __name__ == "__main__":
    asyncio.run(populate())
