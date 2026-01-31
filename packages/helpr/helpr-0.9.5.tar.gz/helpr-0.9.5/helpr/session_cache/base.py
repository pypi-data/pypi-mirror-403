from abc import ABC, abstractmethod


def r_to_str(value):
    # can potentially remove this.
    if isinstance(value, bytes):
        return value.decode('utf-8')
    else:
        return value

default_ttl =  86400*30

class BaseCache(ABC):

    @abstractmethod
    def init_if_not_exists(self, hard_refresh = False):
        pass
    @abstractmethod
    def update_ttl(self):
        pass
    @abstractmethod
    def to_dict(self):
        pass
    @abstractmethod
    def cache_exists(self):
        pass  