from typing                                                      import Optional
from osbot_utils.type_safe.Type_Safe                             import Type_Safe
from osbot_utils.type_safe.primitives.domains.common.safe_str.Safe_Str__Text import Safe_Str__Text
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id import Safe_Str__Id


class Cache__Decorator__Exception(Exception):
    """Base exception for cache decorator operations"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class Cache__Client__Not__Found(Cache__Decorator__Exception):
    """Raised when cache client is not available on the instance"""
    
    def __init__(self, attr_name: str, class_name: str):
        message = f"Cache client '{attr_name}' not found on {class_name}"
        super().__init__(message, {"attr_name": attr_name, "class_name": class_name})


class Cache__Serialization__Error(Cache__Decorator__Exception):
    """Raised when serialization/deserialization fails"""
    
    def __init__(self, operation: str, type_name: str, error: str):
        message = f"Failed to {operation} type {type_name}: {error}"
        super().__init__(message, {"operation": operation, "type": type_name, "error": error})


class Cache__Retrieval__Error(Cache__Decorator__Exception):
    """Raised when cache retrieval fails"""
    
    def __init__(self, namespace: str, cache_hash: str, error: str):
        message = f"Failed to retrieve from cache: {error}"
        super().__init__(message, {"namespace": namespace, "cache_hash": cache_hash, "error": error})


class Cache__Storage__Error(Cache__Decorator__Exception):
    """Raised when cache storage fails"""
    
    def __init__(self, namespace: str, cache_key: str, error: str):
        message = f"Failed to store in cache: {error}"
        super().__init__(message, {"namespace": namespace, "cache_key": cache_key, "error": error})


class Cache__Invalid__Config(Cache__Decorator__Exception):
    """Raised when cache configuration is invalid"""
    
    def __init__(self, field: str, reason: str):
        message = f"Invalid cache configuration for field '{field}': {reason}"
        super().__init__(message, {"field": field, "reason": reason})
