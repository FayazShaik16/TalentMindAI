import os
import psutil
import sqlite3
import time
from typing import Any, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.config import settings
from app.providers.vector.faiss import FAISSProvider
from app.services.agents.orchestrator import orchestrator

class MonitoringService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_system_health(self) -> Dict[str, Any]:
        """
        Calculates status parameters for database, vector store, embedding models, and filesystem resources.
        """
        # 1. Database Health Check
        db_healthy = False
        try:
            # Query a simple raw SQL or test query
            await self.db.execute(select(1))
            db_healthy = True
        except Exception:
            pass

        # 2. Vector Index Health Check
        faiss_provider = FAISSProvider()
        faiss_healthy = True
        faiss_stats = {}
        
        indices_dir = settings.VECTOR_INDEX_DIR if hasattr(settings, "VECTOR_INDEX_DIR") else "vector_indices"
        if os.path.exists(indices_dir):
            for file_name in os.listdir(indices_dir):
                if file_name.endswith("_index.faiss"):
                    collection = file_name.replace("_index.faiss", "")
                    try:
                        stats = await faiss_provider.get_statistics(collection)
                        faiss_stats[collection] = stats
                    except Exception:
                        faiss_healthy = False
        else:
            faiss_healthy = False

        # 3. Embedding SQLite Cache Health
        cache_dir = settings.EMBEDDING_CACHE_DIR if hasattr(settings, "EMBEDDING_CACHE_DIR") else ".embeddings_cache"
        db_path = os.path.join(cache_dir, "embeddings_cache.db")
        cache_count = 0
        cache_healthy = True
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM cache")
                cache_count = cursor.fetchone()[0]
                conn.close()
            except Exception:
                cache_healthy = False
        else:
            cache_healthy = False

        # 4. Telemetry (CPU/RAM/Disk)
        cpu_pct = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage(".")

        return {
            "status": "healthy" if (db_healthy and faiss_healthy and cache_healthy) else "degraded",
            "components": {
                "database": "healthy" if db_healthy else "unhealthy",
                "vector_index": "healthy" if faiss_healthy else "unhealthy",
                "embedding_cache": "healthy" if cache_healthy else "unhealthy"
            },
            "metrics": {
                "faiss_collections_count": len(faiss_stats),
                "faiss_details": faiss_stats,
                "cached_embeddings_count": cache_count,
                "cpu_usage_percent": cpu_pct,
                "ram_usage_percent": mem.percent,
                "ram_available_mb": float(round(mem.available / (1024 * 1024), 2)),
                "disk_free_gb": float(round(disk.free / (1024 * 1024 * 1024), 2))
            }
        }

    async def get_ai_monitoring_stats(self) -> Dict[str, Any]:
        """
        Aggregates agent status, embedding health details, and API latency metrics.
        """
        # Fetch system health metrics
        health = await self.get_system_health()
        
        # Agent status
        agents_health = {}
        for agent_name in orchestrator.list_agents():
            agent = orchestrator.get_agent(agent_name)
            if agent:
                try:
                    status = await agent.health()
                    agents_health[agent_name] = status
                except Exception as e:
                    agents_health[agent_name] = {"status": "error", "message": str(e)}

        return {
            "timestamp": time.time(),
            "embedding_health": {
                "provider": settings.EMBEDDING_PROVIDER,
                "model": settings.EMBEDDING_MODEL,
                "cache_status": health["components"]["embedding_cache"]
            },
            "reranker_health": {
                "model": settings.RERANK_MODEL if hasattr(settings, "RERANK_MODEL") else "BAAI/bge-reranker-base"
            },
            "vector_store_health": {
                "provider": "FAISS CPU",
                "metric_type": settings.VECTOR_METRIC,
                "index_type": settings.VECTOR_INDEX_TYPE,
                "collections": health["metrics"]["faiss_details"]
            },
            "agents_status": agents_health,
            "resources": {
                "cpu_usage_percent": health["metrics"]["cpu_usage_percent"],
                "ram_usage_percent": health["metrics"]["ram_usage_percent"],
                "ram_available_mb": health["metrics"]["ram_available_mb"],
                "disk_free_gb": health["metrics"]["disk_free_gb"]
            }
        }
