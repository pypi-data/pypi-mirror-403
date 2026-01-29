"""AI caching system for DevOS."""

import asyncio
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from .provider import AIRequest, AIResponse


logger = logging.getLogger(__name__)


class AICache:
    """AI response caching system."""
    
    def __init__(self, cache_dir: Optional[Path] = None, max_size_mb: int = 100):
        self.cache_dir = cache_dir or Path.home() / ".devos" / "cache" / "ai"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_mb = max_size_mb
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._cache_index: Dict[str, CacheIndex] = {}
        
        # Load existing cache index
        asyncio.create_task(self._load_cache_index())
    
    async def get(self, request: AIRequest) -> Optional[AIResponse]:
        """Get cached response for request."""
        cache_key = self._generate_cache_key(request)
        
        # Check memory cache first
        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            if not self._is_expired(entry):
                logger.debug(f"Cache hit (memory): {cache_key}")
                # Mark response as cached
                cached_response = entry.response
                cached_response.cached = True
                return cached_response
            else:
                # Remove expired entry
                del self._memory_cache[cache_key]
        
        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                entry = CacheEntry.from_dict(data)
                
                if not self._is_expired(entry):
                    # Load into memory cache
                    self._memory_cache[cache_key] = entry
                    logger.debug(f"Cache hit (disk): {cache_key}")
                    # Mark response as cached
                    cached_response = entry.response
                    cached_response.cached = True
                    return cached_response
                else:
                    # Remove expired file
                    cache_file.unlink()
                    
            except Exception as e:
                logger.warning(f"Failed to load cache entry {cache_key}: {e}")
                try:
                    cache_file.unlink()
                except:
                    pass
        
        return None
    
    async def set(self, request: AIRequest, response: AIResponse) -> None:
        """Cache response for request."""
        cache_key = self._generate_cache_key(request)
        
        # Create cache entry
        entry = CacheEntry(
            request_hash=cache_key,
            response=response,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24),
            access_count=1,
            last_accessed=datetime.now()
        )
        
        # Store in memory cache
        self._memory_cache[cache_key] = entry
        
        # Store on disk
        await self._save_to_disk(cache_key, entry)
        
        # Update cache index
        cache_file = self.cache_dir / f"{cache_key}.json"
        self._cache_index[cache_key] = CacheIndex(
            cache_key=cache_key,
            file_size=cache_file.stat().st_size if cache_file.exists() else 0,
            created_at=entry.created_at,
            last_accessed=entry.last_accessed,
            access_count=1
        )
        
        # Check cache size limit
        await self._enforce_size_limit()
        
        logger.debug(f"Cached response: {cache_key}")
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        # Clear memory cache
        self._memory_cache.clear()
        
        # Clear disk cache
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete cache file {cache_file}: {e}")
        
        # Clear index
        self._cache_index.clear()
        
        logger.info("AI cache cleared")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self._cache_index)
        memory_entries = len(self._memory_cache)
        total_size = sum(index.file_size for index in self._cache_index.values())
        
        # Calculate hit rate (simplified)
        total_accesses = sum(index.access_count for index in self._cache_index.values())
        
        return {
            "total_entries": total_entries,
            "memory_entries": memory_entries,
            "disk_entries": total_entries - memory_entries,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "max_size_mb": self.max_size_mb,
            "total_accesses": total_accesses,
            "cache_dir": str(self.cache_dir)
        }
    
    def _generate_cache_key(self, request: AIRequest) -> str:
        """Generate cache key for request."""
        # Create a normalized representation of the request
        request_data = {
            "query": request.query.strip().lower(),
            "request_type": request.request_type.value,
            "project_path": str(request.context.project_path),
            "language": request.context.language,
            "framework": request.context.framework,
            "model": request.user_preferences.ai_model,
            "temperature": request.user_preferences.temperature
        }
        
        # Create hash
        request_str = json.dumps(request_data, sort_keys=True)
        return hashlib.sha256(request_str.encode()).hexdigest()[:16]
    
    def _is_expired(self, entry: 'CacheEntry') -> bool:
        """Check if cache entry is expired."""
        return datetime.now() > entry.expires_at
    
    async def _save_to_disk(self, cache_key: str, entry: 'CacheEntry') -> None:
        """Save cache entry to disk."""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            data = entry.to_dict()
            cache_file.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            logger.warning(f"Failed to save cache entry {cache_key}: {e}")
    
    async def _load_cache_index(self) -> None:
        """Load cache index from disk."""
        index_file = self.cache_dir / "index.json"
        
        if index_file.exists():
            try:
                data = json.loads(index_file.read_text())
                for cache_key, index_data in data.items():
                    self._cache_index[cache_key] = CacheIndex.from_dict(index_data)
                logger.info(f"Loaded {len(self._cache_index)} cache index entries")
            except Exception as e:
                logger.warning(f"Failed to load cache index: {e}")
    
    async def _save_cache_index(self) -> None:
        """Save cache index to disk."""
        try:
            index_file = self.cache_dir / "index.json"
            data = {key: index.to_dict() for key, index in self._cache_index.items()}
            index_file.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            logger.warning(f"Failed to save cache index: {e}")
    
    async def _enforce_size_limit(self) -> None:
        """Enforce cache size limit by removing old entries."""
        total_size = sum(index.file_size for index in self._cache_index.values())
        max_size_bytes = self.max_size_mb * 1024 * 1024
        
        if total_size <= max_size_bytes:
            return
        
        # Sort entries by last accessed time (LRU)
        sorted_entries = sorted(
            self._cache_index.items(),
            key=lambda x: x[1].last_accessed
        )
        
        # Remove oldest entries until under limit
        removed = 0
        for cache_key, index in sorted_entries:
            if total_size <= max_size_bytes * 0.8:  # Leave 20% headroom
                break
            
            # Remove from memory cache
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
            
            # Remove from disk
            cache_file = self.cache_dir / f"{cache_key}.json"
            try:
                cache_file.unlink()
                total_size -= index.file_size
                removed += 1
            except Exception as e:
                logger.warning(f"Failed to delete cache file {cache_file}: {e}")
            
            # Remove from index
            del self._cache_index[cache_key]
        
        if removed > 0:
            logger.info(f"Removed {removed} old cache entries to enforce size limit")
            await self._save_cache_index()


@dataclass
class CacheEntry:
    """Cache entry containing request and response."""
    request_hash: str
    response: AIResponse
    created_at: datetime
    expires_at: datetime
    access_count: int
    last_accessed: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "request_hash": self.request_hash,
            "response": asdict(self.response),
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary."""
        response_data = data["response"]
        response = AIResponse(**response_data)
        
        return cls(
            request_hash=data["request_hash"],
            response=response,
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            access_count=data["access_count"],
            last_accessed=datetime.fromisoformat(data["last_accessed"])
        )


@dataclass
class CacheIndex:
    """Cache index entry for metadata."""
    cache_key: str
    file_size: int
    created_at: datetime
    last_accessed: datetime
    access_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "cache_key": self.cache_key,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheIndex':
        """Create from dictionary."""
        return cls(
            cache_key=data["cache_key"],
            file_size=data["file_size"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            access_count=data["access_count"]
        )
