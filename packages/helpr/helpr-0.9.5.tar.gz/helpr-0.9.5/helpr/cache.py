import json
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import redis
import redis.asyncio as aioredis

from helpr.json_encoder import EnhancedJSONEncoder


class BulkRedisActionType(int, Enum):
    ADD_TO_SET = 0
    SET_STRING = 1
    DELETE_STRING = 2
    DELETE_FROM_SET = 3
    SAVE_SORTED_SET = 4


class BulkRedisAction:
    def __init__(
        self,
        action_type: BulkRedisActionType,
        key: str,
        value: Optional[str] = None,
        values: Optional[Union[Set[str], Dict[str, float]]] = None,
        expire: Optional[int] = None,
        overwrite: bool = False,
    ):
        """
        Represents a single bulk Redis action to be performed in a pipeline.

        :param action_type: Type of bulk action
        :param key: Redis key
        :param value: Single value for string operations
        :param values: Set or Dict of values for set/sorted set operations
        :param expire: Expiry time in seconds
        :param overwrite: Whether to overwrite existing data
        """
        self.action_type = action_type
        self.key = key

        if action_type == BulkRedisActionType.SET_STRING and value is None:
            raise ValueError("Value cannot be None for SET_STRING action type")

        if (
            action_type
            in (BulkRedisActionType.ADD_TO_SET, BulkRedisActionType.DELETE_FROM_SET)
            and values is None
        ):
            raise ValueError(
                "Values cannot be None for ADD_TO_SET or DELETE_FROM_SET action type"
            )

        if action_type == BulkRedisActionType.SAVE_SORTED_SET and (
            values is None or not isinstance(values, dict)
        ):
            raise ValueError(
                "Values cannot be None and must be a dict for SAVE_SORTED_SET action type"
            )

        self.value = value
        self.values = values
        self.expire = expire
        self.overwrite = overwrite


class RedisHelper:
    def __init__(self, redis_client: redis.Redis,redis_read_client: redis.Redis = None, redis_write_client: redis.Redis = None):
        """
        Initialize the Redis helper with a Redis client.

        :param redis_client: Instance of redis.Redis
        """
        self.redis_client = redis_client
        # Either Pass redis_client or both redis_write_client and redis_read_client
        if redis_client:
            self.redis_read_client = redis_client
            self.redis_write_client = redis_client
        elif not redis_read_client or not redis_write_client:
            raise ValueError("Both read and write redis clients are required")
        else:
            self.redis_write_client = redis_write_client
            self.redis_read_client = redis_read_client

    def _decode(self, value: Optional[bytes]) -> Optional[str]:
        return value.decode("utf-8") if value else None

    def check_connection(self) -> bool:
        """Check if Redis connection is working"""
        try:
            return bool(self.redis_read_client.ping())
        except redis.ConnectionError:
            return False

    # String Operations
    def get_string(self, key: str) -> Optional[str]:
        value = self.redis_read_client.get(key)
        return self._decode(value)

    def get_strings(self, keys: List[str]) -> List[Optional[str]]:
        values = self.redis_read_client.mget(keys)
        return [self._decode(v) for v in values]

    def save_string(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        return bool(self.redis_write_client.set(key, value, ex=expire))

    def save_string_if_not_exists(
        self, key: str, value: str, expire: Optional[int] = None
    ) -> bool:
        return bool(self.redis_write_client.set(key, value, ex=expire, nx=True))

    # Set Operations
    def get_set(self, key: str) -> Set[str]:
        members = self.redis_read_client.smembers(key)
        return {m.decode("utf-8") for m in members}

    def save_set(
        self,
        key: str,
        value: Set[str],
        expire: Optional[int] = None,
        overwrite: bool = False,
    ) -> bool:
        if not value:
            return False
        if overwrite:
            self.redis_write_client.delete(key)
        result = self.redis_write_client.sadd(key, *value)
        if expire is not None:
            self.redis_write_client.expire(key, expire)
        return bool(result)

    def remove_from_set(self, key: str, value: str) -> bool:
        return bool(self.redis_write_client.srem(key, value))

    def is_member_of_set(self, key: str, value: str) -> bool:
        return bool(self.redis_read_client.sismember(key, value))

    def get_set_length(self, key: str) -> int:
        return self.redis_read_client.scard(key)

    # Sorted Set Operations
    def get_sorted_set(
        self, key: str, start: int = 0, end: int = -1, withscores: bool = False
    ) -> List[Union[str, Tuple[str, float]]]:
        results = self.redis_read_client.zrevrange(key, start, end, withscores=withscores)
        if withscores:
            return [(item[0].decode("utf-8"), item[1]) for item in results]
        return [item.decode("utf-8") for item in results]

    def get_sorted_set_by_score(
        self,
        key: str,
        min_score: int = 0,
        max_score: int = -1,
        withscores: bool = False,
    ) -> List[Union[str, Tuple[str, float]]]:
        results = self.redis_read_client.zrevrangebyscore(
            key, max_score, min_score, withscores=withscores
        )
        if withscores:
            return [(item[0].decode("utf-8"), item[1]) for item in results]
        return [item.decode("utf-8") for item in results]

    def save_sorted_set(
        self,
        key: str,
        values: Dict[str, float],
        expire: Optional[int] = None,
        overwrite: bool = False,
    ) -> bool:
        if overwrite:
            self.redis_write_client.delete(key)
        for value, score in values.items():
            self.redis_write_client.zadd(key, {value: score}, incr=True)
        if expire is not None:
            self.redis_write_client.expire(key, expire)
        return True

    # List Operations
    def save_list(
        self,
        key: str,
        values: List[str],
        expire: Optional[int] = None,
        overwrite: bool = False,
    ) -> bool:
        if overwrite:
            self.redis_write_client.delete(key)
        self.redis_write_client.rpush(key, *values)
        if expire is not None:
            self.redis_write_client.expire(key, expire)
        return True

    def get_list(self, key: str) -> List[str]:
        values = self.redis_read_client.lrange(key, 0, -1)
        return [v.decode("utf-8") for v in values]

    # Hash Operations
    def save_hset(
        self, key: str, field: str, value: str, expire: Optional[int] = None
    ) -> bool:
        self.redis_write_client.hset(key, field, value)
        if expire is not None:
            self.redis_write_client.expire(key, expire)
        return True

    def save_hset_bulk(
        self, key: str, mapping: Dict[str, str], expire: Optional[int] = None
    ) -> bool:
        self.redis_write_client.hset(key, mapping=mapping)
        if expire is not None:
            self.redis_write_client.expire(key, expire)
        return True

    def get_hset(self, key: str, field: str) -> Optional[str]:
        value = self.redis_read_client.hget(key, field)
        return self._decode(value)

    def get_hset_bulk(self, key: str, fields: List[str]) -> List[Optional[str]]:
        values = self.redis_read_client.hmget(key, fields)
        return [self._decode(v) for v in values]

    def get_hmset(self, key: str) -> Dict[str, str]:
        result = self.redis_read_client.hgetall(key)
        return {k.decode("utf-8"): v.decode("utf-8") for k, v in result.items()}

    def del_hmset_field(self, key: str, field: str) -> bool:
        return bool(self.redis_write_client.hdel(key, field))

    def del_hmset_fields(self, key: str, fields: List[str]) -> bool:
        return bool(self.redis_write_client.hdel(key, *fields))

    def save_hmset(self, key: str, mapping: dict, expire: Optional[int] = None):
        """Save multiple hash fields at once"""
        
        self.redis_write_client.hset(key, mapping=mapping)
        if expire is not None:
            self.redis_write_client.expire(key, expire)

    def delete(self, key: str) -> bool:
        """Delete a key"""
        return bool(self.redis_write_client.delete(key))

    # Bulk Operations
    def save_strings(self, actions: List[BulkRedisAction]) -> List[Any]:
        with self.redis_write_client.pipeline() as pipe:
            expiry_map = {}
            for action in actions:
                key = action.key
                if action.action_type == BulkRedisActionType.SET_STRING:
                    pipe.set(key, action.value)
                    if action.expire is not None:
                        expiry_map[key] = action.expire
                elif action.action_type == BulkRedisActionType.DELETE_STRING:
                    pipe.delete(key)
                elif action.action_type == BulkRedisActionType.DELETE_FROM_SET:
                    pipe.srem(key, *action.values)
                elif action.action_type == BulkRedisActionType.ADD_TO_SET:
                    pipe.sadd(key, *action.values)
                    if action.expire is not None:
                        expiry_map[key] = action.expire
                elif action.action_type == BulkRedisActionType.SAVE_SORTED_SET:
                    if action.overwrite:
                        pipe.delete(key)
                    for value, score in action.values.items():
                        pipe.zadd(key, {value: score}, incr=True)
                    if action.expire is not None:
                        expiry_map[key] = action.expire

            for key, expire in expiry_map.items():
                pipe.expire(key, expire)

            # Execute pipeline and check for errors
            results = pipe.execute()

            # Check for any failed operations
            failed_operations = []
            for i, result in enumerate(results):
                if result is False or (isinstance(result, int) and result == 0):
                    failed_operations.append(i)

            if failed_operations:
                raise RuntimeError(
                    f"Pipeline operations failed at indices: {failed_operations}"
                )

            return results

    def bulk_insert_lists(self, data: Dict[str, List[Any]], ttl: int) -> None:
        with self.redis_write_client.pipeline() as pipe:
            for key, values in data.items():
                pipe.delete(key)
                pipe.rpush(key, *values)
                pipe.expire(key, ttl)
            pipe.execute()

    # Key Operations
    def delete_key(self, key: str) -> bool:
        return bool(self.redis_write_client.delete(key))

    def delete_keys(self, pattern: str) -> None:
        """Delete all keys matching a pattern"""
        cursor = 0
        while True:
            cursor, keys = self.redis_write_client.scan(
                cursor=cursor, match=pattern, count=5000
            )
            if keys:
                self.redis_write_client.delete(*keys)
            if cursor == 0:
                break

    def exists(self, key: str) -> bool:
        return bool(self.redis_read_client.exists(key))

    def rename_key(self, old_key: str, new_key: str) -> bool:
        self.redis_write_client.rename(old_key, new_key)
        return True

    def update_ttl(self, key: str, expire: int) -> bool:
        return bool(self.redis_write_client.expire(key, expire))

    def get_ttl(self, key: str) -> Optional[int]:
        ttl = self.redis_read_client.ttl(key)
        return None if ttl == -1 else ttl

    # Lock Operations
    def get_lock(self, key: str, timeout: Optional[float] = None) -> redis.lock.Lock:
        return self.redis_write_client.lock(key, timeout=timeout)

    def zunionstore(
        self, destination: str, keys: List[str], aggregate: Optional[str] = None
    ) -> int:
        """
        Perform a union of multiple sorted sets and store the result in a destination key.

        :param destination: The key to store the result.
        :param keys: List of source sorted set keys.
        :param aggregate: Aggregation function ('SUM', 'MIN', 'MAX'). Defaults to None (SUM).
        :return: The number of elements in the resulting sorted set.
        """
        return self.redis_write_client.zunionstore(destination, keys, aggregate=aggregate)

    # JSON Operations
    def save_json(
        self, key: str, value: Any, expire: Optional[int] = None, overwrite: bool = True
    ) -> bool:
        """
        Save a JSON-serializable object into Redis as a string.
        """

        try:
            data = json.dumps(value, cls=EnhancedJSONEncoder)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Value is not JSON serializable: {e}")

        if overwrite:
            return bool(self.redis_write_client.set(key, data, ex=expire))
        return bool(self.redis_write_client.set(key, data, ex=expire, nx=True))

    def get_json(self, key: str) -> Optional[Any]:
        """
        Retrieve and decode JSON object stored in Redis.
        """
        value = self.redis_read_client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    def remove_from_list(self, key: str, value: str, count: int = 1) -> int:
        """
        Remove elements from a list (equivalent to LREM)
        Args:
            key: Redis key
            value: Value to remove
            count: Number of occurrences to remove (default 1)
        Returns:
            Number of elements removed
        """
        return self.redis_write_client.lrem(key, count, value)

    def scan_keys(self, pattern: str, count: int = 1000) -> List[str]:
        """
        Scan for keys matching a pattern using SCAN command
        Args:
            pattern: Pattern to match (with wildcards)
            count: Number of keys to return per iteration
        Returns:
            List of matching keys
        """
        all_keys = []
        cursor = 0

        while True:
            cursor, keys = self.redis_read_client.scan(
                cursor=cursor, match=pattern, count=count
            )
            
            processed_keys = [
                key.decode("utf-8") if isinstance(key, bytes) else str(key)
                for key in keys
            ]
            all_keys.extend(processed_keys)

            if cursor == 0:
                break

        return all_keys

    def get_multiple_values_pipeline(self, keys: List[str]) -> List[Optional[str]]:
        """
        Get multiple values using pipeline for better performance
        Args:
            keys: List of Redis keys
        Returns:
            List of values (None for non-existent keys)
        """
        if not keys:
            return []

        with self.redis_read_client.pipeline() as pipe:
            for key in keys:
                pipe.get(key)
            values = pipe.execute()

        return [v.decode("utf-8") if v else None for v in values]

    def get_multiple_json_pipeline(self, keys: List[str]) -> List[Optional[Any]]:
        """
        Get multiple JSON objects using pipeline
        Args:
            keys: List of Redis keys
        Returns:
            List of JSON objects (None for non-existent keys)
        """
        values = self.get_multiple_values_pipeline(keys)
        results = []

        for value in values:
            if value is None:
                results.append(None)
            else:
                try:
                    results.append(json.loads(value))
                except json.JSONDecodeError:
                    results.append(None)

        return results

    def atomic_json_update(
        self, key: str, update_func: Callable, expire: Optional[int] = None
    ) -> bool:
        """
        Atomically update a JSON object using a Lua script
        Args:
            key: Redis key
            update_func: Function that takes current value and returns updated value
            expire: TTL in seconds
        Returns:
            True if successful, False otherwise
        """

        lua_script = """
        local key = KEYS[1]
        local expire_time = ARGV[1]
        local current_value = redis.call('GET', key)

        if current_value then
            -- Return current value to Python for processing
            return current_value
        else
            return nil
        end
        """

        try:
            current_value = self.redis_write_client.eval(lua_script, 1, key, expire or 0)

            if current_value:
                current_obj = json.loads(current_value.decode("utf-8"))
            else:
                current_obj = None

            updated_obj = update_func(current_obj)

            if updated_obj is not None:
                return self.save_json(key, updated_obj, expire=expire)

            return False

        except Exception:
            return False

    def bulk_pipeline_operations(self, operations: List[dict]) -> List[Any]:
        """
        Execute multiple Redis operations in a pipeline
        Args:
            operations: List of dicts with 'operation', 'key', and optional 'args'
                       Example: [{'operation': 'get', 'key': 'mykey'},
                                {'operation': 'set', 'key': 'mykey2', 'args': ['value']}]
        Returns:
            List of results from each operation
        """
        if not operations:
            return []

        with self.redis_write_client.pipeline() as pipe:
            for op in operations:
                operation = op.get("operation")
                key = op.get("key")
                args = op.get("args", [])

                if operation == "get":
                    pipe.get(key)
                elif operation == "set":
                    pipe.set(key, *args)
                elif operation == "delete":
                    pipe.delete(key)
                elif operation == "ttl":
                    pipe.ttl(key)
                elif operation == "lrange":
                    pipe.lrange(key, *args)
                elif operation == "lrem":
                    pipe.lrem(key, *args)
                elif operation == "rpush":
                    pipe.rpush(key, *args)
                elif operation == "expire":
                    pipe.expire(key, *args)
                # Add more operations as needed

            return pipe.execute()

    def append_to_list(
        self, key: str, values: List[str], expire: Optional[int] = None
    ) -> int:
        """
        Append values to the end of a list
        Args:
            key: Redis key
            values: List of values to append
            expire: TTL in seconds
        Returns:
            Length of list after append
        """
        result = self.redis_write_client.rpush(key, *values)
        if expire is not None:
            self.redis_write_client.expire(key, expire)
        return result

    def prepend_to_list(
        self, key: str, values: List[str], expire: Optional[int] = None
    ) -> int:
        """
        Prepend values to the beginning of a list
        Args:
            key: Redis key
            values: List of values to prepend
            expire: TTL in seconds
        Returns:
            Length of list after prepend
        """
        result = self.redis_write_client.lpush(key, *values)
        if expire is not None:
            self.redis_write_client.expire(key, expire)
        return result

    def get_list_range(self, key: str, start: int = 0, end: int = -1) -> List[str]:
        """
        Get a range of elements from a list
        Args:
            key: Redis key
            start: Start index
            end: End index (-1 for end of list)
        Returns:
            List of elements in range
        """
        values = self.redis_read_client.lrange(key, start, end)
        return [v.decode("utf-8") for v in values]

    def get_list_length(self, key: str) -> int:
        """
        Get the length of a list
        Args:
            key: Redis key
        Returns:
            Length of the list
        """
        return self.redis_read_client.llen(key)


class AsyncRedisHelper:
    """Async version of RedisHelper for non-blocking Redis operations"""

    def __init__(self, redis_client: aioredis.Redis, redis_read_client: aioredis.Redis = None, redis_write_client: aioredis.Redis = None):
        """
        Initialize the Async Redis helper with an async Redis client.

        :param redis_client: Instance of redis.asyncio.Redis
        :param redis_read_client: Optional separate read client
        :param redis_write_client: Optional separate write client
        """
        self.redis_client = redis_client
        # Either Pass redis_client or both redis_write_client and redis_read_client
        if redis_client:
            self.redis_read_client = redis_client
            self.redis_write_client = redis_client
        elif not redis_read_client or not redis_write_client:
            raise ValueError("Both read and write redis clients are required")
        else:
            self.redis_write_client = redis_write_client
            self.redis_read_client = redis_read_client

    def _decode(self, value: Optional[bytes]) -> Optional[str]:
        return value.decode("utf-8") if value else None

    async def check_connection(self) -> bool:
        """Check if Redis connection is working"""
        try:
            return bool(await self.redis_read_client.ping())
        except aioredis.ConnectionError:
            return False

    async def ping(self) -> bool:
        """Ping Redis to check connection"""
        return await self.redis_read_client.ping()

    # String Operations
    async def get_string(self, key: str) -> Optional[str]:
        value = await self.redis_read_client.get(key)
        return self._decode(value)

    async def get_strings(self, keys: List[str]) -> List[Optional[str]]:
        values = await self.redis_read_client.mget(keys)
        return [self._decode(v) for v in values]

    async def save_string(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        return bool(await self.redis_write_client.set(key, value, ex=expire))

    async def save_string_if_not_exists(
        self, key: str, value: str, expire: Optional[int] = None
    ) -> bool:
        return bool(await self.redis_write_client.set(key, value, ex=expire, nx=True))

    # Set Operations
    async def get_set(self, key: str) -> Set[str]:
        members = await self.redis_read_client.smembers(key)
        return {m.decode("utf-8") for m in members}

    async def save_set(
        self,
        key: str,
        value: Set[str],
        expire: Optional[int] = None,
        overwrite: bool = False,
    ) -> bool:
        if not value:
            return False
        if overwrite:
            await self.redis_write_client.delete(key)
        result = await self.redis_write_client.sadd(key, *value)
        if expire is not None:
            await self.redis_write_client.expire(key, expire)
        return bool(result)

    async def remove_from_set(self, key: str, value: str) -> bool:
        return bool(await self.redis_write_client.srem(key, value))

    async def is_member_of_set(self, key: str, value: str) -> bool:
        return bool(await self.redis_read_client.sismember(key, value))

    async def get_set_length(self, key: str) -> int:
        return await self.redis_read_client.scard(key)

    # Sorted Set Operations
    async def get_sorted_set(
        self, key: str, start: int = 0, end: int = -1, withscores: bool = False
    ) -> List[Union[str, Tuple[str, float]]]:
        results = await self.redis_read_client.zrevrange(key, start, end, withscores=withscores)
        if withscores:
            return [(item[0].decode("utf-8"), item[1]) for item in results]
        return [item.decode("utf-8") for item in results]

    async def save_sorted_set(
        self,
        key: str,
        values: Dict[str, float],
        expire: Optional[int] = None,
        overwrite: bool = False,
    ) -> bool:
        if overwrite:
            await self.redis_write_client.delete(key)
        for value, score in values.items():
            await self.redis_write_client.zadd(key, {value: score}, incr=True)
        if expire is not None:
            await self.redis_write_client.expire(key, expire)
        return True

    # List Operations
    async def save_list(
        self,
        key: str,
        values: List[str],
        expire: Optional[int] = None,
        overwrite: bool = False,
    ) -> bool:
        if overwrite:
            await self.redis_write_client.delete(key)
        await self.redis_write_client.rpush(key, *values)
        if expire is not None:
            await self.redis_write_client.expire(key, expire)
        return True

    async def get_list(self, key: str) -> List[str]:
        values = await self.redis_read_client.lrange(key, 0, -1)
        return [v.decode("utf-8") for v in values]

    # Hash Operations
    async def save_hset(
        self, key: str, field: str, value: str, expire: Optional[int] = None
    ) -> bool:
        await self.redis_write_client.hset(key, field, value)
        if expire is not None:
            await self.redis_write_client.expire(key, expire)
        return True

    async def save_hset_bulk(
        self, key: str, mapping: Dict[str, str], expire: Optional[int] = None
    ) -> bool:
        await self.redis_write_client.hset(key, mapping=mapping)
        if expire is not None:
            await self.redis_write_client.expire(key, expire)
        return True

    async def get_hset(self, key: str, field: str) -> Optional[str]:
        value = await self.redis_read_client.hget(key, field)
        return self._decode(value)

    async def get_hset_bulk(self, key: str, fields: List[str]) -> List[Optional[str]]:
        values = await self.redis_read_client.hmget(key, fields)
        return [self._decode(v) for v in values]

    async def get_hmset(self, key: str) -> Dict[str, str]:
        result = await self.redis_read_client.hgetall(key)
        return {k.decode("utf-8"): v.decode("utf-8") for k, v in result.items()}

    async def del_hmset_field(self, key: str, field: str) -> bool:
        return bool(await self.redis_write_client.hdel(key, field))

    async def del_hmset_fields(self, key: str, fields: List[str]) -> bool:
        return bool(await self.redis_write_client.hdel(key, *fields))

    async def save_hmset(self, key: str, mapping: dict, expire: Optional[int] = None):
        """Save multiple hash fields at once"""
        await self.redis_write_client.hset(key, mapping=mapping)
        if expire is not None:
            await self.redis_write_client.expire(key, expire)

    async def delete(self, key: str) -> bool:
        """Delete a key"""
        return bool(await self.redis_write_client.delete(key))

    async def delete_key(self, key: str) -> bool:
        """Delete a key (alias for delete)"""
        return bool(await self.redis_write_client.delete(key))

    async def delete_keys(self, pattern: str) -> None:
        """Delete all keys matching a pattern"""
        cursor = 0
        while True:
            cursor, keys = await self.redis_write_client.scan(
                cursor=cursor, match=pattern, count=5000
            )
            if keys:
                await self.redis_write_client.delete(*keys)
            if cursor == 0:
                break

    async def exists(self, key: str) -> bool:
        return bool(await self.redis_read_client.exists(key))

    async def rename_key(self, old_key: str, new_key: str) -> bool:
        await self.redis_write_client.rename(old_key, new_key)
        return True

    async def update_ttl(self, key: str, expire: int) -> bool:
        return bool(await self.redis_write_client.expire(key, expire))

    async def get_ttl(self, key: str) -> Optional[int]:
        ttl = await self.redis_read_client.ttl(key)
        return None if ttl == -1 else ttl

    # JSON Operations
    async def save_json(
        self, key: str, value: Any, expire: Optional[int] = None, overwrite: bool = True
    ) -> bool:
        """Save a JSON-serializable object into Redis as a string."""
        try:
            data = json.dumps(value, cls=EnhancedJSONEncoder)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Value is not JSON serializable: {e}")

        if overwrite:
            return bool(await self.redis_write_client.set(key, data, ex=expire))
        return bool(await self.redis_write_client.set(key, data, ex=expire, nx=True))

    async def get_json(self, key: str) -> Optional[Any]:
        """Retrieve and decode JSON object stored in Redis."""
        value = await self.redis_read_client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    async def scan_keys(self, pattern: str, count: int = 1000) -> List[str]:
        """Scan for keys matching a pattern using SCAN command"""
        all_keys = []
        cursor = 0

        while True:
            cursor, keys = await self.redis_read_client.scan(
                cursor=cursor, match=pattern, count=count
            )

            processed_keys = [
                key.decode("utf-8") if isinstance(key, bytes) else str(key)
                for key in keys
            ]
            all_keys.extend(processed_keys)

            if cursor == 0:
                break

        return all_keys

    async def get_multiple_values_pipeline(self, keys: List[str]) -> List[Optional[str]]:
        """Get multiple values using pipeline for better performance"""
        if not keys:
            return []

        async with self.redis_read_client.pipeline() as pipe:
            for key in keys:
                pipe.get(key)
            values = await pipe.execute()

        return [v.decode("utf-8") if v else None for v in values]

    async def get_multiple_json_pipeline(self, keys: List[str]) -> List[Optional[Any]]:
        """Get multiple JSON objects using pipeline"""
        values = await self.get_multiple_values_pipeline(keys)
        results = []

        for value in values:
            if value is None:
                results.append(None)
            else:
                try:
                    results.append(json.loads(value))
                except json.JSONDecodeError:
                    results.append(None)

        return results

    async def append_to_list(
        self, key: str, values: List[str], expire: Optional[int] = None
    ) -> int:
        """Append values to the end of a list"""
        result = await self.redis_write_client.rpush(key, *values)
        if expire is not None:
            await self.redis_write_client.expire(key, expire)
        return result

    async def get_list_range(self, key: str, start: int = 0, end: int = -1) -> List[str]:
        """Get a range of elements from a list"""
        values = await self.redis_read_client.lrange(key, start, end)
        return [v.decode("utf-8") for v in values]

    async def get_list_length(self, key: str) -> int:
        """Get the length of a list"""
        return await self.redis_read_client.llen(key)

    async def get_sorted_set_by_score(
        self,
        key: str,
        min_score: int = 0,
        max_score: int = -1,
        withscores: bool = False,
    ) -> List[Union[str, Tuple[str, float]]]:
        """Get sorted set members by score range"""
        results = await self.redis_read_client.zrevrangebyscore(
            key, max_score, min_score, withscores=withscores
        )
        if withscores:
            return [(item[0].decode("utf-8"), item[1]) for item in results]
        return [item.decode("utf-8") for item in results]

    async def get_lock(self, key: str, timeout: Optional[float] = None):
        """Get a distributed lock"""
        return self.redis_write_client.lock(key, timeout=timeout)

    async def zunionstore(
        self, destination: str, keys: List[str], aggregate: Optional[str] = None
    ) -> int:
        """Perform a union of multiple sorted sets and store the result"""
        return await self.redis_write_client.zunionstore(destination, keys, aggregate=aggregate)

    async def remove_from_list(self, key: str, value: str, count: int = 1) -> int:
        """Remove elements from a list"""
        return await self.redis_write_client.lrem(key, count, value)

    async def prepend_to_list(
        self, key: str, values: List[str], expire: Optional[int] = None
    ) -> int:
        """Prepend values to the beginning of a list"""
        result = await self.redis_write_client.lpush(key, *values)
        if expire is not None:
            await self.redis_write_client.expire(key, expire)
        return result

    async def atomic_json_update(
        self, key: str, update_func: Callable, expire: Optional[int] = None
    ) -> bool:
        """Atomically update a JSON object using a Lua script"""
        lua_script = """
        local key = KEYS[1]
        local expire_time = ARGV[1]
        local current_value = redis.call('GET', key)

        if current_value then
            -- Return current value to Python for processing
            return current_value
        else
            return nil
        end
        """

        try:
            current_value = await self.redis_write_client.eval(lua_script, 1, key, expire or 0)

            if current_value:
                current_obj = json.loads(current_value.decode("utf-8"))
            else:
                current_obj = None

            updated_obj = update_func(current_obj)

            if updated_obj is not None:
                return await self.save_json(key, updated_obj, expire=expire)

            return False

        except Exception:
            return False

    async def bulk_pipeline_operations(self, operations: List[dict]) -> List[Any]:
        """Execute multiple Redis operations in a pipeline"""
        if not operations:
            return []

        async with self.redis_write_client.pipeline() as pipe:
            for op in operations:
                operation = op.get("operation")
                key = op.get("key")
                args = op.get("args", [])

                if operation == "get":
                    pipe.get(key)
                elif operation == "set":
                    pipe.set(key, *args)
                elif operation == "delete":
                    pipe.delete(key)
                elif operation == "ttl":
                    pipe.ttl(key)
                elif operation == "lrange":
                    pipe.lrange(key, *args)
                elif operation == "lrem":
                    pipe.lrem(key, *args)
                elif operation == "rpush":
                    pipe.rpush(key, *args)
                elif operation == "expire":
                    pipe.expire(key, *args)

            return await pipe.execute()

    async def bulk_insert_lists(self, data: Dict[str, List[Any]], ttl: int) -> None:
        """Bulk insert multiple lists with TTL"""
        async with self.redis_write_client.pipeline() as pipe:
            for key, values in data.items():
                pipe.delete(key)
                pipe.rpush(key, *values)
                pipe.expire(key, ttl)
            await pipe.execute()

    # Async version of save_strings bulk operations
    async def save_strings(self, actions: List[BulkRedisAction]) -> List[Any]:
        """Perform bulk Redis operations in a pipeline"""
        async with self.redis_write_client.pipeline() as pipe:
            expiry_map = {}
            for action in actions:
                key = action.key
                if action.action_type == BulkRedisActionType.SET_STRING:
                    pipe.set(key, action.value)
                    if action.expire is not None:
                        expiry_map[key] = action.expire
                elif action.action_type == BulkRedisActionType.DELETE_STRING:
                    pipe.delete(key)
                elif action.action_type == BulkRedisActionType.DELETE_FROM_SET:
                    pipe.srem(key, *action.values)
                elif action.action_type == BulkRedisActionType.ADD_TO_SET:
                    pipe.sadd(key, *action.values)
                    if action.expire is not None:
                        expiry_map[key] = action.expire
                elif action.action_type == BulkRedisActionType.SAVE_SORTED_SET:
                    if action.overwrite:
                        pipe.delete(key)
                    for value, score in action.values.items():
                        pipe.zadd(key, {value: score}, incr=True)
                    if action.expire is not None:
                        expiry_map[key] = action.expire

            for key, expire in expiry_map.items():
                pipe.expire(key, expire)

            # Execute pipeline and check for errors
            results = await pipe.execute()

            # Check for any failed operations
            failed_operations = []
            for i, result in enumerate(results):
                if result is False or (isinstance(result, int) and result == 0):
                    failed_operations.append(i)

            if failed_operations:
                raise RuntimeError(
                    f"Pipeline operations failed at indices: {failed_operations}"
                )

            return results
