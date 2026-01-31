import inspect
from typing                                                                                             import Any, Callable, Optional, Type, Tuple
from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client                          import Cache__Service__Client
from osbot_utils.type_safe.Type_Safe                                                                    import Type_Safe
from osbot_utils.type_safe.primitives.domains.cryptography.safe_str.Safe_Str__Cache_Hash                import Safe_Str__Cache_Hash
from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path                       import Safe_Str__File__Path
from osbot_utils.type_safe.type_safe_core.decorators.type_safe                                          import type_safe
from osbot_utils.decorators.methods.cache_on_self                                                       import cache_on_self
from mgraph_ai_service_cache_client.client.decorator.cache_operations.Cache__Decorator__Operations      import Cache__Decorator__Operations
from mgraph_ai_service_cache_client.client.decorator.cache_operations.Cache__Key__Builder               import Cache__Key__Builder
from mgraph_ai_service_cache_client.client.decorator.schemas.Schema__Cache__Decorator__Config           import Schema__Cache__Decorator__Config
from mgraph_ai_service_cache_client.client.decorator.schemas.enums.Enum__Cache__Decorator__Mode         import Enum__Cache__Decorator__Mode
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Data_Type                          import Enum__Cache__Data_Type

class Decorator__Cache(Type_Safe):                                                              # Helper class for cache decoration - contains all caching logic
    
    cache_service_client : Cache__Service__Client = None
    _operations          : Cache__Decorator__Operations      = None
    _key_builder         : Cache__Key__Builder    = None

    @cache_on_self
    def operations(self) -> Cache__Decorator__Operations:                                                  # Get or create cache operations handler
        if not self._operations:
            self._operations = Cache__Decorator__Operations(cache_service_client = self.cache_service_client)
        return self._operations

    @cache_on_self
    def key_builder(self) -> Cache__Key__Builder:                                               # Get or create key builder
        if not self._key_builder:
            self._key_builder = Cache__Key__Builder()
        return self._key_builder

    @type_safe
    def is_available(self) -> bool:                                                             # Check if cache is available and configured
        return self.cache_service_client is not None

    @type_safe
    def get_status(self) -> dict:                                                               # Get cache status information
        if not self.is_available():
            return {"available": False, "reason": "No cache service configured"}
        return self.operations().get_client_status()

    def execute_cached(self,                                                                    # Execute a method with caching logic
                       func   : Callable                       ,                                # The method to execute
                       args   : tuple                          ,                                # Positional arguments (includes self)
                       kwargs : dict                           ,                                # Keyword arguments
                       config : Schema__Cache__Decorator__Config                                # Cache configuration
                  ) -> Any:                                                                     # Return value from cache or method execution
        
        self_instance = args[0]
        class_name    = type(self_instance).__name__
        method_name   = func.__name__
        
        cache_key, cache_hash = self._build_cache_key_and_hash(func        = func       ,       # Build cache key and hash
                                                               args        = args       ,
                                                               kwargs      = kwargs     ,
                                                               config      = config     ,
                                                               class_name  = class_name ,
                                                               method_name = method_name)

        if config.mode != Enum__Cache__Decorator__Mode.READ_ONLY:                               # Try to retrieve from cache (unless in READ_ONLY mode)
            cached_result = self._try_retrieve(func       = func      ,
                                               config     = config    ,
                                               cache_hash = cache_hash)
            if cached_result is not None:
                return cached_result

        result = func(*args, **kwargs)                                                          # Execute the actual method

        if config.mode == Enum__Cache__Decorator__Mode.ENABLED:                             # Store result in cache (only in ENABLED mode)
            self._try_store(config    = config   ,
                            cache_key = cache_key,
                            result    = result   )

        return result


    def _build_cache_key_and_hash(self,                                                         # Build cache key and hash from method parameters
                                  func       : Callable                       ,
                                  args       : tuple                          ,
                                  kwargs     : dict                           ,
                                  config     : Schema__Cache__Decorator__Config,
                                  class_name : str                            ,
                                  method_name: str
                             ) -> Tuple[Safe_Str__File__Path, Safe_Str__Cache_Hash]:                                              # Returns (cache_key, cache_hash)
        
        sig        = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        params_dict = dict(bound_args.arguments)                                                # Remove 'self' from parameters
        params_dict.pop('self', None)
        
        cache_key  = self.key_builder().build_cache_key(config      = config     ,
                                                        class_name  = class_name ,
                                                        method_name = method_name,
                                                        params      = params_dict)
        
        cache_hash = self.key_builder().build_cache_hash(data=cache_key)


        return cache_key, cache_hash        # todo: replace with Type_Safe class

    def _try_retrieve(self,                                                                     # Try to retrieve from cache, returns None on any error
                      func      : Callable                       ,
                      config    : Schema__Cache__Decorator__Config,
                      cache_hash: str
                 ) -> Any:

        # return_type                  = _extract_type_hint(func)
        # #data_type, type_safe_class   = _determine_cache_data_type(return_type)

        result = self.operations().retrieve(namespace       = config.namespace           ,
                                            cache_hash      = cache_hash                 )
        return result

    def _try_store(self,                                                                        # Try to store in cache, logs errors but doesn't raise
                   config   : Schema__Cache__Decorator__Config,
                   cache_key: str                             ,
                   result   : Any
              ) -> bool:
        if result is None:
            return False
        result = self.operations().store(namespace       = config.namespace,
                                         cache_key       = cache_key       ,
                                         data            = result          ,
                                         config          = config          )
        return result

    def _try_invalidate(self,                                                                   # Try to invalidate cache entry, logs errors but doesn't raise
                        config    : Schema__Cache__Decorator__Config,
                        cache_hash: str
                   ) -> bool:
        result = self.operations().invalidate(namespace  = config.namespace,
                                              cache_hash = cache_hash      )
        return result

# todo: should these methods be here?
def _extract_type_hint(func: Callable) -> Optional[type]:                                       # Extract return type hint from function signature
    try:
        sig = inspect.signature(func)
        if sig.return_annotation != inspect.Signature.empty:
            return sig.return_annotation
        return None
    except Exception:
        return None

# todo: doesn't OSBot-Utils already have methods for this?
def _determine_cache_data_type(return_type: Type                                                # Determine cache data type from Python type hint
                          ) -> tuple[Enum__Cache__Data_Type, Optional[Type[Type_Safe]]]:        # Returns (data_type, type_safe_class or None)
    
    if return_type is None:                                                                     # Default to JSON if no type hint
        return (Enum__Cache__Data_Type.JSON, None)
    
    if return_type is str:                                                                      # String type
        return (Enum__Cache__Data_Type.STRING, None)
    
    if return_type is bytes:                                                                    # Binary type
        return (Enum__Cache__Data_Type.BINARY, None)
    
    if return_type is dict:                                                                     # Dict type
        return (Enum__Cache__Data_Type.JSON, None)
    
    if isinstance(return_type, type) and issubclass(return_type, Type_Safe):                    # Type_Safe subclass
        return (Enum__Cache__Data_Type.TYPE_SAFE, return_type)
    
    from typing import get_origin, get_args, Union                                              # Handle Optional and Union types
    origin = get_origin(return_type)
    if origin is Union:
        args = get_args(return_type)
        non_none_args = [arg for arg in args if arg is not type(None)]                          # Filter out NoneType
        if len(non_none_args) == 1:
            return _determine_cache_data_type(non_none_args[0])                                 # Recurse with the non-None type
    
    return (Enum__Cache__Data_Type.JSON, None)                                                  # Default to JSON for complex types