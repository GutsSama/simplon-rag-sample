import asyncio
import os
import sys
import time
import uuid
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from rag.config.settings import get_settings
from rag.rag.agent.graph import build_graph
from rag.db.models.conversation import Conversation

async def run_test(name, question, graph, db_session, conversation_id):
    print(f"\n>>> TEST: {name}")
    print(f"Question: {question}")
    
    start_time = time.perf_counter()
    
    # Run the graph in streaming mode to see progress
    inputs = {
        "user_message": question,
        "conversation_id": conversation_id,
        "retry_count": 0
    }
    
    last_state = {}
    async for event in graph.astream(inputs, stream_mode="updates"):
        for node_name, state_update in event.items():
            node_time = time.perf_counter() - start_time
            print(f"  [+{node_time:.2f}s] Node '{node_name}' completed.")
            if state_update:
                last_state.update(state_update)
    
    final_state = last_state
    
    end_time = time.perf_counter()
    total_latency = end_time - start_time
    
    print(f"Response: {final_state.get('answer', 'NO ANSWER')[:200]}...")
    print(f"Sources: {final_state.get('sources', [])}")
    print(f"In Scope: {final_state.get('in_scope', 'N/A')}")
    print(f"--- Timings internes ---")
    print(f"  Guard Route: {final_state.get('guard_route_duration', 0):.2f}s")
    print(f"  Retrieval  : {final_state.get('retrieve_duration', 0):.2f}s")
    print(f"  Generation : {final_state.get('generate_duration', 0):.2f}s")
    print(f"  Evaluation : {final_state.get('evaluate_duration', 0):.2f}s")
    print(f"------------------------")
    print(f"Latence Totale (script): {total_latency:.2f}s")
    
    return {
        "name": name,
        "latency": total_latency,
        "in_scope": final_state.get("in_scope"),
        "has_sources": len(final_state.get("sources", [])) > 0
    }

async def main():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Create a test conversation
    async with async_session() as session:
        conv = Conversation(metadata_={})
        session.add(conv)
        await session.commit()
        await session.refresh(conv)
        conv_id = conv.id

        graph = build_graph(session)
        
        tests = [
            ("Simple (Prérequis)", "Quels sont les prérequis de la formation IA ?"),
            ("Transverse (Compétences)", "Quelles compétences transversales sont évaluées dans le parcours IA ?"),
            ("Piège (Médecine)", "Quel est le règlement pour les étudiants en médecine ?"),
        ]
        
        results = []
        for name, q in tests:
            res = await run_test(name, q, graph, session, conv_id)
            results.append(res)
    
    print("\n" + "="*30)
    print("RESUME DES TESTS DE PERFORMANCE")
    print("="*30)
    for r in results:
        status = "✅ PASS" if r['latency'] < 10 else "⚠️ SLOW"
        print(f"{r['name']}: {r['latency']:.2f}s - {status}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
