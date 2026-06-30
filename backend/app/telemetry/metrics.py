import time
import os
import psutil
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

class TelemetryMetrics:
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.error_count = 0

    def increment_errors(self):
        self.error_count += 1

    def get_system_metrics(self) -> dict:
        """
        Gathers CPU percent, RSS memory consumption, thread count, and uptime stats.
        """
        memory_info = self.process.memory_info()
        return {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_usage_bytes": memory_info.rss,
            "memory_usage_mb": memory_info.rss / (1024 * 1024),
            "process_threads": self.process.num_threads(),
            "uptime_seconds": time.time() - psutil.boot_time(),
            "tracked_error_count": self.error_count,
        }

    async def check_database(self, db: AsyncSession) -> bool:
        """
        Executes a simple SELECT 1 database ping to check connection health.
        """
        try:
            result = await db.execute(text("SELECT 1"))
            return result.scalar() == 1
        except Exception:
            return False

telemetry = TelemetryMetrics()
