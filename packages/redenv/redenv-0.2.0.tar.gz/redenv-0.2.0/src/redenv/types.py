from dataclasses import dataclass, field
from typing import Literal, Dict, Any

LogPreference = Literal["none", "low", "high"]

@dataclass
class UpstashConfig:
    url: str
    token: str

@dataclass
class CacheConfig:
    ttl: int = 300
    swr: int = 86400

@dataclass
class EnvConfig:
    override: bool = True

class CacheEntry:
    def __init__(self, value: Any, created_at: float):
        self.value = value
        self.created_at = created_at

@dataclass
class RedenvOptions:
    project: str
    token_id: str
    token: str
    upstash: UpstashConfig
    environment: str = "development"
    cache: CacheConfig = field(default_factory=CacheConfig)
    env: EnvConfig = field(default_factory=EnvConfig)
    log: LogPreference = "low"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RedenvOptions':
        upstash_data = data.get("upstash", {})
        upstash = UpstashConfig(
            url=upstash_data.get("url", ""),
            token=upstash_data.get("token", "")
        )
        
        cache_data = data.get("cache", {})
        cache = CacheConfig(
            ttl=cache_data.get("ttl", 300),
            swr=cache_data.get("swr", 86400)
        )

        env_data = data.get("env", {})
        env = EnvConfig(
            override=env_data.get("override", True)
        )

        return cls(
            project=data.get("project", ""),
            token_id=data.get("token_id", data.get("tokenId", "")),
            token=data.get("token", ""),
            upstash=upstash,
            environment=data.get("environment", "development"),
            cache=cache,
            env=env,
            log=data.get("log", "low")
        )
