import redis
from typing import Optional


class SessionCacheConfig:
    """Configuration class for SessionCache to manage Redis client."""

    _default_redis_client: Optional[redis.Redis] = None
    _key_format: str = "sesh:ss_data:{session_id}"  # Match Sesh format
    
    @classmethod
    def configure(cls, redis_client: redis.Redis, key_format: Optional[str] = None):
        """
        Configure the default Redis client for SessionCache operations.

        Args:
            redis_client: Redis client instance to use for all SessionCache operations
            key_format: Optional key format string with {session_id} placeholder.
                       Default: "sesh:ss_data:{session_id}"
                       Example: "custom_prefix:ss_data:{session_id}"
        """
        if not isinstance(redis_client, redis.Redis):
            raise ValueError("redis_client must be an instance of redis.Redis")
        cls._default_redis_client = redis_client
        if key_format is not None:
            if "{session_id}" not in key_format:
                raise ValueError("key_format must contain {session_id} placeholder")
            cls._key_format = key_format
    
    @classmethod
    def get_redis_client(cls) -> redis.Redis:
        """
        Get the configured Redis client.
        
        Returns:
            Redis client instance
            
        Raises:
            ValueError: If no Redis client has been configured
        """
        if cls._default_redis_client is None:
            raise ValueError(
                "Redis client not configured. Call SessionCacheConfig.configure(redis_client) first."
            )
        return cls._default_redis_client
    
    @classmethod
    def is_configured(cls) -> bool:
        """
        Check if Redis client has been configured.

        Returns:
            True if configured, False otherwise
        """
        return cls._default_redis_client is not None

    @classmethod
    def get_key_format(cls) -> str:
        """
        Get the configured session key format.

        Returns:
            Key format string with {session_id} placeholder
        """
        return cls._key_format