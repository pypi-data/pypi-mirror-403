import logging
from typing                                                                                      import Union, Dict, Type
from osbot_fast_api.services.registry.Fast_API__Service__Registry                                import fast_api__service__registry
from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client                   import Cache__Service__Client
from osbot_utils.type_safe.Type_Safe                                                             import Type_Safe
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id                  import Safe_Str__Id
from osbot_utils.type_safe.primitives.domains.cryptography.safe_str.Safe_Str__Cache_Hash         import Safe_Str__Cache_Hash
from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path                import Safe_Str__File__Path
from osbot_utils.type_safe.type_safe_core.decorators.type_safe                                   import type_safe
from mgraph_ai_service_cache_client.client.decorator.schemas.Schema__Cache__Decorator__Config    import Schema__Cache__Decorator__Config
from mgraph_ai_service_cache_client.client.decorator.schemas.Schema__Cache__Decorator__Data      import Schema__Cache__Decorator__Data
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Data_Type                   import Enum__Cache__Data_Type

logger = logging.getLogger(__name__)


class Cache__Decorator__Operations(Type_Safe):                                                 # Handles all cache operations for the decorator.

    cache_service_client: Cache__Service__Client

    @type_safe
    def retrieve(self                               ,                   # Retrieve data from cache and deserialize it.
                 namespace       : Safe_Str__Id           ,             # Cache namespace
                 cache_hash      : Safe_Str__Cache_Hash   ,             # Hash to retrieve
            ) -> Union[Type_Safe, Dict, str]:                           # Deserialized data or None if not found

        if not self.cache_service_client:
            return None

        with self.cache_service_client.retrieve() as _:                # Use the cache client to retrieve data

            data_json  = _.retrieve__hash__cache_hash__json    (cache_hash = cache_hash, namespace=namespace)
            result = None
            if data_json:
                try:
                    cache_decorator_data = Schema__Cache__Decorator__Data.from_json(data_json)
                except ValueError as error:
                    raise Exception(f"Failed to load data from cache : {error.args[0]}") from None

                data = cache_decorator_data.data

                if cache_decorator_data.data_type == Enum__Cache__Data_Type.TYPE_SAFE:
                    result = cache_decorator_data.type_safe_class(**data)
                elif cache_decorator_data.data_type == Enum__Cache__Data_Type.STRING:
                    result = data                                                                # these should work automatically
                elif cache_decorator_data.data_type == Enum__Cache__Data_Type.JSON:
                    result = data


            # if   data_type == Enum__Cache__Data_Type.STRING:
            #     result     =  _.retrieve__hash__cache_hash__string (cache_hash = cache_hash, namespace=namespace)
            #
            # elif data_type == Enum__Cache__Data_Type.JSON:
            #     result     = _.retrieve__hash__cache_hash__json    (cache_hash = cache_hash, namespace=namespace)
            #
            # elif data_type == Enum__Cache__Data_Type.TYPE_SAFE:
            #     data_json  = _.retrieve__hash__cache_hash__json    (cache_hash = cache_hash, namespace=namespace)
            #     if type_safe_class:
            #         result = type_safe_class.from_json(data_json)
            #
            # elif data_type == Enum__Cache__Data_Type.BINARY:
            #     result     = _.retrieve__hash__cache_hash__binary  (cache_hash = cache_hash, namespace=namespace)

        return result

    @type_safe
    def store(self,                                                 # Store data in cache after serialization.
             namespace      : Safe_Str__Id                      ,   # Cache namespace
             cache_key      : Safe_Str__File__Path              ,   # Cache key for storage
             data           : Union[Type_Safe, dict, str],          # Data to store (one of the 3 types supported by cache service and dict)
             config         : Schema__Cache__Decorator__Config      # Cache configuration
        ) -> bool:                                                  # returns True if stored successfully, False otherwise

        if not self.cache_service_client:
            return False

        with self.cache_service_client as cache_client:
            if isinstance(data,Type_Safe):                                          # if we received a Type_Save object
                type_safe_class = type(data)
                data_type       = Enum__Cache__Data_Type.TYPE_SAFE
                data            = data.json()                                       # convert it to a dict via .json()
            elif isinstance(data,str):
                type_safe_class = None
                data_type       = Enum__Cache__Data_Type.STRING
            else:
                type_safe_class = None
                data_type       = Enum__Cache__Data_Type.JSON

            cache_decorator_data = Schema__Cache__Decorator__Data(cache_key       = cache_key       ,                # cache data is stored as Schema__Cache__Decorator__Data
                                                                  data            = data            ,
                                                                  data_type       = data_type       ,
                                                                  type_safe_class = type_safe_class )
            cache_data      = cache_decorator_data.json()
            json_field_path = 'cache_key'
            kwargs = dict(namespace       = namespace      ,
                          strategy        = config.strategy,
                          cache_key       = cache_key      ,
                          body            = cache_data     ,
                          file_id         = config.file_id ,
                          json_field_path = json_field_path)

            result = cache_client.store().store__json__cache_key  (**kwargs)

            if result and hasattr(result, 'cache_id'):
                return True
            else:
                return False

    @type_safe
    def invalidate(self,                                # Invalidate (delete) a cache entry.
                  namespace  : Safe_Str__Id        ,    # Cache namespace
                  cache_hash : Safe_Str__Cache_Hash     # Hash to invalidate
                 ) -> bool:                             # True if invalidated successfully, False otherwise

        if not self.cache_service_client:
            return False

        with self.cache_service_client as cache_client:        # First, we need to get the cache_id from the hash

            result = cache_client.retrieve().retrieve__hash__cache_hash__cache_id(cache_hash = cache_hash,    # Try to retrieve to get the cache_id
                                                                                  namespace  = namespace )
            if not result:
                return False
            cache_id = result.get('cache_id')                                                           # found cache_id for this cache_hash

            delete_result = cache_client.delete().delete__cache_id(cache_id  = str(cache_id),           # Now delete using the cache_id
                                                                   namespace = str(namespace))

        if delete_result:
            return True
        else:
            return False


    @type_safe
    def exists(self,                                                    # Check if a cache entry exists.
               namespace  : Safe_Str__Id        ,                       # Cache namespace
               cache_hash : Safe_Str__Cache_Hash                        # Hash to check
          ) -> bool:                                                    # True if exists, False otherwise
        if not self.cache_service_client:
            return False


        with self.cache_service_client as cache_client:
            result = cache_client.retrieve().retrieve__hash__cache_hash(cache_hash = cache_hash,
                                                                        namespace  = namespace )

        return result is not None

    @type_safe
    def get_client_status(self                                          # Get status information about the cache client.
                     ) -> dict:                                         # Dictionary with status information
        # if not self.client_cache_service:
        #     return {"available": False, "reason": "No client configured"}

        service_config        = fast_api__service__registry.config(Cache__Service__Client)
        with self.cache_service_client as cache_client:        # Try to get server info
            info = cache_client.info().status()
            return { "available": True                     ,
                     "mode"     : service_config.mode.value,
                     "info"     : info                     }
