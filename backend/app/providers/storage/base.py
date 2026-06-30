from abc import ABC, abstractmethod

class BaseStorageProvider(ABC):
    """
    Abstract interface wrapping object storage read/write operations.
    """
    @abstractmethod
    async def upload(self, bucket: str, path: str, content: bytes, content_type: str | None = None) -> str:
        """
        Upload binary payload to a bucket namespace and return download URL.
        """
        pass

    @abstractmethod
    async def download(self, bucket: str, path: str) -> bytes:
        """
        Download raw binary content of a stored file.
        """
        pass

    @abstractmethod
    async def delete(self, bucket: str, path: str) -> bool:
        """
        Delete file from object storage.
        """
        pass
