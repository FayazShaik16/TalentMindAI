import os
import json
import hashlib
from typing import Any
from app.core.config.config import settings
from app.core.logging.logging import logger

class DiskCache:
    def __init__(self, cache_dir: str = settings.CACHE_DIR):
        self.cache_dir = cache_dir
        # Ensure target cache folder is created
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        # Use MD5 hash of key for filename safety
        key_hash = hashlib.md5(key.encode("utf-8")).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.json")

    def get(self, key: str) -> Any | None:
        """
        Reads value from JSON disk cache file. Returns None on cache miss.
        """
        path = self._get_cache_path(key)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
                return payload.get("value")
        except Exception as e:
            logger.warning("cache_read_error", key=key, error=str(e))
            return None

    def set(self, key: str, value: Any) -> bool:
        """
        Writes key-value parameters to a local JSON file.
        """
        path = self._get_cache_path(key)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"key": key, "value": value}, f, default=str, indent=2)
            return True
        except Exception as e:
            logger.warning("cache_write_error", key=key, error=str(e))
            return False

    def delete(self, key: str) -> bool:
        """
        Deletes a cached item if it exists.
        """
        path = self._get_cache_path(key)
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except Exception as e:
                logger.warning("cache_delete_error", key=key, error=str(e))
                return False
        return False

    def clear(self) -> bool:
        """
        Clears all cached JSON files in the cache directory.
        """
        try:
            for file in os.listdir(self.cache_dir):
                if file.endswith(".json"):
                    os.remove(os.path.join(self.cache_dir, file))
            return True
        except Exception as e:
            logger.error("cache_clear_error", error=str(e))
            return False

disk_cache = DiskCache()
