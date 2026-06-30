import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.providers.vector.faiss import FAISSProvider
from app.services.embedding_service import embedding_service

async def show_stats():
    provider = FAISSProvider()
    collections = ["summary", "career", "projects", "skills", "education"]
    
    print("=== FAISS Collections Statistics ===")
    print(f"{'Collection':<12} | {'Trained':<8} | {'Metric':<8} | {'Index Type':<10} | {'Dim':<5} | {'Vectors Count':<14}")
    print("-" * 70)
    
    for col in collections:
        stats = await provider.get_statistics(col)
        if stats.get("status") == "collection_not_found":
            print(f"{col:<12} | {'[NOT CREATED]':<53}")
        else:
            trained = "Yes" if stats.get("is_trained") else "No"
            print(f"{col:<12} | {trained:<8} | {stats.get('metric_type'):<8} | {stats.get('index_type'):<10} | {stats.get('dimension'):<5} | {stats.get('ntotal'):<14}")
            
    # Get SQLite cache count
    cache_count = 0
    try:
        import sqlite3
        with sqlite3.connect(embedding_service.db_path) as conn:
            cursor = conn.execute("SELECT count(*) FROM cache")
            cache_count = cursor.fetchone()[0]
    except Exception:
        pass
        
    print(f"\nEmbedding Cache Entries Count (SQLite DB): {cache_count}")

def main():
    asyncio.run(show_stats())

if __name__ == "__main__":
    main()
