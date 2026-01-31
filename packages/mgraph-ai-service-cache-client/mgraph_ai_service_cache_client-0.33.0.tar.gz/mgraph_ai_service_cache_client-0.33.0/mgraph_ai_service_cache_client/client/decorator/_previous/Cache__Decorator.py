# import functools
# import inspect
# import logging
# from typing                                                                                     import Any, Callable, Optional
# from osbot_utils.helpers.cache.Cache__Hash__Generator                                           import Cache__Hash__Generator
#
# from osbot_utils.type_safe.Type_Safe import Type_Safe
#
# from mgraph_ai_service_cache_client.client.decorator.schemas.Schema__Cache__Decorator__Config   import Schema__Cache__Decorator__Config
# from mgraph_ai_service_cache_client.client.decorator.schemas.enums.Enum__Cache__Decorator__Mode import Enum__Cache__Decorator__Mode
#
# logger = logging.getLogger(__name__)
#
#
# def cache_response(config: Schema__Cache__Decorator__Config) -> Callable:                           # Decorator to cache method responses using cache service
#     key_generator  = Cache__Decorator__Key__Generator()                                             # Create key generator instance
#     hash_generator = Cache__Hash__Generator()                                                       # Create hash generator instance
#
#     def decorator(func: Callable) -> Callable:
#
#         @functools.wraps(func)
#         def wrapper(*args, **kwargs) -> Any:
#
#             if not config.enabled or config.mode == Enum__Cache__Decorator__Mode.DISABLED:     # Check if caching is disabled
#                 return func(*args, **kwargs)                                    # Execute method without caching
#
#             self_arg = args[0] if args else None                                # Get 'self' (first positional arg)
#             if not self_arg:                                                    # No 'self' means it's not a method
#                 return func(*args, **kwargs)
#
#             cache_client = getattr(self_arg, config.cache_attr_name, None)      # Get cache client from instance
#             if not cache_client:                                                # No cache client available
#                 logger.debug(f"Cache client '{config.cache_attr_name}' not found on {type(self_arg).__name__}, executing without cache")
#                 return func(*args, **kwargs)
#
#             sig = inspect.signature(func)                                       # Get method signature
#             bound_args = sig.bind(*args, **kwargs)                              # Bind arguments to parameters
#             bound_args.apply_defaults()                                         # Fill in default values
#
#             class_name = type(self_arg).__name__                                # Extract class and method names
#             method_name = func.__name__
#
#             params_dict = dict(bound_args.arguments)                            # Convert bound arguments to dict
#             params_dict.pop('self', None)                                       # Remove 'self' from params
#
#             cache_key = key_generator.generate(config      = config,            # Generate cache key
#                                                class_name  = class_name,
#                                                method_name = method_name,
#                                                **params_dict)
#
#             cache_hash = hash_generator.from_string(cache_key)                  # Generate cache hash
#
#             if config.mode != Enum__Cache__Decorator__Mode.READ_ONLY:          # Try to retrieve from cache (unless READ_ONLY mode)
#                 cached_result = _retrieve_from_cache(cache_client               ,
#                                                      config                     ,
#                                                      cache_hash                 ,
#                                                      func                       )
#
#                 if cached_result is not None:                                   # Cache hit
#                     logger.debug(f"Cache HIT for {class_name}.{method_name}() with key: {cache_key}")
#                     return cached_result
#
#             logger.debug(f"Cache MISS for {class_name}.{method_name}() with key: {cache_key}")
#
#             result = func(*args, **kwargs)
#
#             if config.mode == Enum__Cache__Decorator__Mode.ENABLED:        # Store result in cache (only in ENABLED mode)
#                 _store_in_cache(cache_client                                ,
#                                config                                       ,
#                                cache_key                                    ,
#                                result                                       )
#
#             return result
#
#
#         return wrapper
#
#     return decorator
#
#
# def _retrieve_from_cache(cache_client : Any,                                    # Retrieve cached response from cache service
#                          config       : Schema__Cache__Decorator__Config,
#                          cache_hash   : str,
#                          func         : Callable
#                     ) -> Optional[Any]:
#     """Retrieve cached result and deserialize to original type"""
#
#     try:
#         result = cache_client.cache_client.retrieve().retrieve__hash__cache_hash(cache_hash = cache_hash,
#                                                                                  namespace  = config.namespace)
#
#         if not result:                                                          # Not found in cache
#             return None
#
#         body = result.get('body')                                               # Extract body from result
#
#         if body is None:                                                        # No body means cache miss
#             return None
#
#         response_type = _get_response_type(func)                                # Get expected response type from function signature
#
#         if response_type and hasattr(response_type, 'from_json'):               # Deserialize Type_Safe response
#             return response_type.from_json(body)
#
#         return body                                                             # Return raw body if can't deserialize
#
#     except Exception as e:
#         logger.warning(f"Error retrieving from cache: {e}")
#         return None
#
#
# def _store_in_cache(cache_client : Any,                                         # Store response in cache service
#                     config       : Schema__Cache__Decorator__Config,
#                     cache_key    : str,
#                     result       : Any
#                ) -> None:
#     """Store result in cache, serializing Type_Safe objects"""
#
#     if result is None:                                                          # Don't cache None results
#         return
#
#     try:
#
#         if isinstance(result, Type_Safe):                                       # Serialize Type_Safe objects to JSON
#             body = result.json()
#         else:
#             body = result                                                       # Store other types as-is
#
#         cache_client.cache_client.store().store__json__cache_key(data         = body,
#                                                                  namespace    = config.namespace,
#                                                                  strategy     = config.strategy,
#                                                                  cache_key    = cache_key,
#                                                                  file_id      = config.file_id)
#
#         logger.debug(f"Stored result in cache with key: {cache_key}")
#
#     except Exception as e:
#         logger.warning(f"Error storing in cache: {e}")
#
#
# def _invalidate_cache(cache_client : Any,                                       # Invalidate cache entry (delete from cache)
#                       config       : Schema__Cache__Decorator__Config,
#                       cache_hash   : str
#                  ) -> None:
#     """Remove cache entry when method execution fails"""
#
#     try:
#         cache_client.cache_client.delete().delete__hash__cache_hash(cache_hash = cache_hash,
#                                                                     namespace  = config.namespace)
#
#         logger.debug(f"Invalidated cache for hash: {cache_hash}")
#
#     except Exception as e:
#         logger.warning(f"Error invalidating cache: {e}")
#
#
# def _get_response_type(func: Callable) -> Optional[type]:                       # Extract response type from function signature
#     """Get the return type annotation from function signature"""
#
#     sig = inspect.signature(func)
#
#     if sig.return_annotation != inspect.Signature.empty:                        # Check if return annotation exists
#         return sig.return_annotation
#
#     return None
