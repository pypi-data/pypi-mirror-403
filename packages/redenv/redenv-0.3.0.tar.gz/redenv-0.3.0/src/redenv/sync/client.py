import time
from typing import Dict, Any, Optional, Literal
from upstash_redis import Redis
from cachetools import LRUCache
from ..types import RedenvOptions
from ..secrets import Secrets
from .utils import fetch_and_decrypt, populate_env, log, error, set_secret, get_secret_version
from ..errors import RedenvError

class CacheEntry:
    def __init__(self, value: Any, created_at: float):
        self.value = value
        self.created_at = created_at

class Redenv:
    def __init__(self, options: Dict[str, Any]):
        self.options = RedenvOptions.from_dict(options)
        self.validate_options()
        
        self._cache = LRUCache(maxsize=1000)
        
        self.redis = Redis(
            url=self.options.upstash.url,
            token=self.options.upstash.token
        )

    def validate_options(self):
        if not self.options.project:
            raise RedenvError("Missing required configuration option: project", "MISSING_CONFIG")
        if not self.options.token_id:
            raise RedenvError("Missing required configuration option: token_id", "MISSING_CONFIG")
        if not self.options.token:
            raise RedenvError("Missing required configuration option: token", "MISSING_CONFIG")
        if not self.options.upstash.url or not self.options.upstash.token:
            raise RedenvError("Missing required configuration option: upstash", "MISSING_CONFIG")

    def _get_cache_key(self) -> str:
        return f"redenv:{self.options.project}:{self.options.environment}"

    def _get_secrets(self) -> Secrets:
        key = self._get_cache_key()
        entry = self._cache.get(key)
        now = time.time()
        
        ttl_seconds = self.options.cache.ttl
        swr_seconds = self.options.cache.swr
        
        def fetch_fresh() -> Secrets:
            try:
                log("Fetching fresh secrets...", self.options.log)
                secrets = fetch_and_decrypt(self.redis, self.options)
                self._cache[key] = CacheEntry(secrets, time.time())
                populate_env(secrets, self.options)
                return secrets
            except Exception as e:
                error(f"Failed to fetch secrets: {e}", self.options.log)
                raise e

        if entry:
            age = now - entry.created_at
            
            if age < ttl_seconds:
                log("Cache hit (Fresh).", self.options.log)
                return entry.value
            
            elif age < (ttl_seconds + swr_seconds):
                # In Sync mode, we can't easily background refresh without threads.
                # Option 1: Block and refresh (Safe)
                # Option 2: Return stale (Fast, but never updates)
                # We choose Option 1 for correctness in Sync scripts.
                log("Cache stale. Refreshing (Blocking)...", self.options.log)
                return fetch_fresh()
            else:
                log("Cache expired. Fetching fresh...", self.options.log)
                return fetch_fresh()
        else:
            log("Cache miss. Fetching fresh...", self.options.log)
            return fetch_fresh()

    def init(self):
        """
        Initializes the environment with secrets.
        Alias for load().
        """
        self.load()

    def load(self) -> Secrets:
        """
        Fetches, caches, and injects secrets into the environment.
        
        Args:
            override: If True (default), overwrites existing environment variables.
        """
        secrets = self._get_secrets()
        
        # Ensure env is populated
        populate_env(secrets, self.options)
        
        return secrets

    def set(self, key: str, value: str):
        """
        Adds or updates a secret.
        """
        if not key or not value:
            raise RedenvError("Key and value are required.", "INVALID_INPUT")
            
        try:
            set_secret(self.redis, self.options, key, value)
            log(f'Successfully set secret for key "{key}".', self.options.log)
            
            cache_key = self._get_cache_key()
            if cache_key in self._cache:
                del self._cache[cache_key]
                
        except Exception as e:
            msg = str(e)
            error(f"Failed to set secret: {msg}", self.options.log)
            raise RedenvError(f"Failed to set secret: {msg}", "UNKNOWN_ERROR")

    def get_version(self, key: str, version: int, mode: Literal["id", "index"] = "id") -> Optional[str]:
        """
        Fetches a specific version of a secret.
        
        Args:
            key: The secret key.
            version: The version ID or index.
            mode: "id" (default) uses positive version numbers, negative for index from end.
                  "index" treats version as a 0-based array index (0=latest).
        """
        return get_secret_version(self.redis, self.options, self._cache, key, version, mode)
