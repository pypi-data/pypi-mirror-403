import functools
import logging
from typing                                                                                     import Any, Callable
from mgraph_ai_service_cache_client.client.decorator.schemas.Schema__Cache__Decorator__Config   import Schema__Cache__Decorator__Config
from mgraph_ai_service_cache_client.client.decorator.schemas.enums.Enum__Cache__Decorator__Mode import Enum__Cache__Decorator__Mode
from mgraph_ai_service_cache_client.client.decorator.Decorator__Cache                           import Decorator__Cache
from mgraph_ai_service_cache_client.client.decorator.exceptions.Cache__Decorator__Exceptions    import Cache__Invalid__Config

logger = logging.getLogger(__name__)


def cache_response(config: Schema__Cache__Decorator__Config) -> Callable:                       # Decorator that caches method responses transparently

    if not config:                                                                              # Validate configuration
        raise Cache__Invalid__Config("config", "Configuration cannot be None")

    if not config.namespace:
        raise Cache__Invalid__Config("namespace", "Namespace must be specified")

    def decorator(func: Callable) -> Callable:                                                  # Inner decorator function

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:                                                    # Wrapper function that implements caching logic

            if not config.enabled or config.mode == Enum__Cache__Decorator__Mode.DISABLED:     # Quick exit if caching is disabled
                return func(*args, **kwargs)

            if not args:                                                                        # Must have 'self' as first argument
                logger.debug(f"No 'self' argument found for {func.__name__}, executing without cache")
                return func(*args, **kwargs)

            self_instance = args[0]

            if not isinstance(self_instance, object) or not hasattr(self_instance.__class__, func.__name__):
                return func(*args, **kwargs)                                                    # Not an instance method, execute without caching

            cache_helper = _get_cache_helper(self_instance, config)                             # Get the Decorator__Cache from instance

            if not cache_helper:
                return func(*args, **kwargs)                                                    # No cache available, execute without caching

            return cache_helper.execute_cached(func   = func  ,                                 # Delegate all caching logic to Decorator__Cache
                                               args   = args  ,
                                               kwargs = kwargs,
                                               config = config)

        wrapper._cache_config  = config                                                         # Add metadata to the wrapper for introspection
        wrapper._cache_enabled = True
        wrapper._original_func = func

        return wrapper

    return decorator


def _get_cache_helper(instance: object,                                                         # Get Decorator__Cache from instance
                      config  : Schema__Cache__Decorator__Config
                 ) -> Decorator__Cache:                                                         # Returns Decorator__Cache or None

    if not hasattr(instance, config.cache_attr_name):
        return None

    cache_attr = getattr(instance, config.cache_attr_name)

    if isinstance(cache_attr, Decorator__Cache):                                                # Already a Decorator__Cache
        if cache_attr.is_available():
            return cache_attr
        return None

    if hasattr(cache_attr, 'client'):                                                           # Legacy: Client__Cache__Service
        from mgraph_ai_service_cache_client.client.Client__Cache__Service import Client__Cache__Service
        if isinstance(cache_attr, Client__Cache__Service):
            return Decorator__Cache(client_cache_service=cache_attr)

    return None


def disable_cache_for_method(func: Callable) -> Callable:                                       # Decorator to explicitly disable caching for a method
    if hasattr(func, '_cache_enabled'):
        func._cache_enabled = False
    return func


def get_cache_config(func: Callable) -> Schema__Cache__Decorator__Config:                       # Get the cache configuration from a decorated method
    if hasattr(func, '_cache_config'):
        return func._cache_config
    return None


def is_cache_decorated(func: Callable) -> bool:                                                 # Check if a method has cache decoration
    return hasattr(func, '_cache_enabled') and func._cache_enabled