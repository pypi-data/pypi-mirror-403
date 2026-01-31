from datetime import datetime
from typing import Optional, Tuple, Union
import uuid
import redis
from helpr.cache import RedisHelper
from helpr.exceptions import AppException
from helpr.session_cache.base import BaseCache, r_to_str, default_ttl
from helpr.session_cache.config import SessionCacheConfig

class SessionCache (BaseCache):

    __session_data_key = None
    __session_id = None
    __user_id = None

    def __init__(self, session_id, user_id = None, redis_client: redis.Redis = None):
        if not session_id:
            raise ValueError("No session_id provided")
        if redis_client is None:
            redis_client = SessionCacheConfig.get_redis_client()
        self.cache = RedisHelper(redis_client=redis_client)
        self.__session_id = session_id
        # Use configurable key format (default: sesh:ss_data:{session_id})
        key_format = SessionCacheConfig.get_key_format()
        self.__session_data_key = key_format.format(session_id=self.__session_id)
        if self.cache.exists(self.__session_data_key):
            existing_user = self.get_data(key="user_id")
            if existing_user and existing_user != user_id:
                raise AppException(message = "User id <> Session mismatch. You don't have access to this session!", 
                         error_code = 1101, http_code=401)
        self.__user_id = user_id
    @staticmethod
    def create_session_id(client_id:str = None) -> str:
        redis_client = SessionCacheConfig.get_redis_client()
        cache = RedisHelper(redis_client=redis_client)
        new_uuid = str(uuid.uuid4())
        
        if not client_id:
            return new_uuid
        else:
            is_valid_client_id = len(client_id)>8 and bool(client_id and all(c.isalnum() or c == "-" for c in client_id))

            if not is_valid_client_id:
                raise AppException(message = "Invalid client_id format", error_code = 1102, http_code=401)
            
            client_id_key = f"sesh:ci_{client_id}"

            if cache.save_string_if_not_exists(client_id_key, new_uuid, 120):  # cache for 2 minutes
                return new_uuid
            elif existing_uuid := cache.get_string(client_id_key):
                return existing_uuid
            else:# So, the only case where save_string_if_not_exists would return False and get_string would also return None is if the key expired in the small amount of time between the two function calls. This is highly unlikely, but it is technically possible if the expiration time is very short and/or the system is under heavy load.
                cache.save_string_if_not_exists(client_id_key, new_uuid, 120)
                return new_uuid    

    @staticmethod
    def validate_session_id(session_id) -> bool:
        if not session_id:
            return False
        # Use configurable key format (default: sesh:ss_data:{session_id})
        key_format = SessionCacheConfig.get_key_format()
        session_key = key_format.format(session_id=session_id)
        redis_client = SessionCacheConfig.get_redis_client()
        cache = RedisHelper(redis_client=redis_client)
        if not cache.exists(session_key):
            return False
        return True
    
    @staticmethod
    def validate_visit_id(session_id, cache=None) -> bool:
        if cache is None:
            session_cache = SessionCache(session_id=session_id)
            cache = session_cache.get_data(keys=["last_heartbeat"])
        last_heartbeat = cache.get("last_heartbeat") if cache.get("last_heartbeat") else ""
        try:
            last_heartbeat_time = datetime.strptime(last_heartbeat, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            return False
        # Using a default TTL of 30 minutes since Config.VISIT_ID_TTL is not defined
        visit_id_ttl = 1800  # 30 minutes in seconds
        if visit_id_ttl > (datetime.now() - last_heartbeat_time).total_seconds():
            return True
        return False
    
   

    def create_visit_id(self, client_id: str = None) -> Tuple[str, bool]:
        redis_client = SessionCacheConfig.get_redis_client()
        cache = RedisHelper(redis_client=redis_client)
        new_uuid = str(uuid.uuid4())
        
        if not client_id:
            return new_uuid, True
        else:
            is_valid_client_id = len(client_id)>8 and bool(client_id and all(c.isalnum() or c == "-" for c in client_id))

            if not is_valid_client_id:
                raise AppException(message = "Invalid client_id format", error_code = 1102, http_code=401)
            
            client_id_key = f"ci_{client_id}_visit_id"

            if cache.save_string_if_not_exists(client_id_key, new_uuid, 120):  # cache for 2 minutes
                return new_uuid, True
            elif existing_uuid := cache.get_string(client_id_key):
                return existing_uuid, False
            else:# So, the only case where save_string_if_not_exists would return False and get_string would also return None is if the key expired in the small amount of time between the two function calls. This is highly unlikely, but it is technically possible if the expiration time is very short and/or the system is under heavy load.
                cache.save_string_if_not_exists(client_id_key, new_uuid, 120)
                return new_uuid, True

    def init_if_not_exists(self, force_refresh = False, client_id: Optional[str]=None) -> Tuple[str, int]:
        cache = self.get_data(keys=["last_heartbeat", "visit_id", "visit_count"])
        visit_id_validator = self.validate_visit_id(session_id=self.__session_id, cache=cache)
        # Handle None value safely - cache.get might return None even with default
        visit_count_raw = cache.get("visit_count")
        visit_count = int(visit_count_raw) if visit_count_raw is not None else 0
        visit_id = cache.get("visit_id", None)
        if not visit_id_validator or not visit_id:
            visit_id, is_updated = self.create_visit_id(client_id=client_id)
            if is_updated:
                visit_count += 1
            
        if not self.cache.exists(self.__session_data_key):  
            self.update_session_data_with_dict({"session_id":self.__session_id,
                                                "created_at": str(datetime.now()),
                                                "last_heartbeat": str(datetime.now()),
                                                "visit_id": visit_id, 
                                                "visit_count": 1 if visit_count == 0 else visit_count})
            self.update_ttl()
        else:
            self.update_session_data_with_dict({"visit_id": visit_id, "visit_count": 1 if visit_count == 0 else visit_count})

        if self.__user_id:
            self.update_session_data("user_id", self.__user_id)

        return visit_id, visit_count

    def update_ttl(self):
        self.cache.update_ttl(self.__session_data_key, default_ttl)
    
    def update_session_data(self, key, value):
        if not key or not value:
            raise ValueError("Key or value is empty")
        self.cache.save_hset(self.__session_data_key, key, value)

    def update_session_data_with_dict(self, dict):
        if any(not k or not v for k, v in dict.items()):
            raise ValueError("Dictionary contains empty keys or values")
        self.cache.save_hmset(self.__session_data_key, dict)
    
    def remove_session_data(self, keys: list):
        if not keys or not any(keys):
            raise ValueError("No key provided")
        self.cache.del_hmset_fields(self.__session_data_key, keys)

    def delete_session(self):
        self.cache.delete(self.__session_data_key)
    
    def cache_exists(self):
        return self.cache.exists(self.__session_data_key)

    def to_dict(self):
        return self.get_data()

    def get_data(self, key: Optional[str] = None, keys: Optional[list] = None):
        if key:
            return r_to_str(self.cache.get_hset(self.__session_data_key, key))
        elif keys:
            data = self.cache.get_hset_bulk(self.__session_data_key, keys)
            return {k: r_to_str(v) for k, v in zip(keys, data)}
        else:
            data = self.cache.get_hmset(self.__session_data_key)
            return {r_to_str(k): r_to_str(v) for k, v in data.items()}
        
