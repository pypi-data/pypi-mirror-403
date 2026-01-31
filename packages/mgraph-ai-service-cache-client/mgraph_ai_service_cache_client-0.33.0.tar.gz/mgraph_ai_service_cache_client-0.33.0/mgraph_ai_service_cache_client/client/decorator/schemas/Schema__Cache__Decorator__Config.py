from typing                                                                                     import List
from osbot_utils.type_safe.Type_Safe                                                            import Type_Safe
from osbot_utils.type_safe.primitives.core.Safe_UInt                                            import Safe_UInt
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id                 import Safe_Str__Id
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Json__Field_Path   import Safe_Str__Json__Field_Path
from mgraph_ai_service_cache_client.client.decorator.schemas.enums.Enum__Cache__Decorator__Mode import Enum__Cache__Decorator__Mode
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Store__Strategy            import Enum__Cache__Store__Strategy

CACHE__DECORATOR__CONFIG__ENABLED         = True
CACHE__DECORATOR__CONFIG__FILE_ID         = "response"
CACHE__DECORATOR__CONFIG__ATTRIBUTE_NAME  = "decorator__cache"
CACHE__DECORATOR__CONFIG__USE_CLASS_NAME  = True
CACHE__DECORATOR__CONFIG__USE_METHOD_NAME = True


class Schema__Cache__Decorator__Config(Type_Safe):                                                      # Configuration for cache decorator behavior
    namespace           : Safe_Str__Id                                                                  # Cache namespace (e.g., "semantic-text/transformations")
    enabled             : bool                              = CACHE__DECORATOR__CONFIG__ENABLED         # Master switch for caching
    mode                : Enum__Cache__Decorator__Mode      = Enum__Cache__Decorator__Mode.ENABLED
    strategy            : Enum__Cache__Store__Strategy      = Enum__Cache__Store__Strategy.KEY_BASED
    key_fields          : List[Safe_Str__Json__Field_Path]                                                 # Method param names to include in cache key hash
    use_class_name      : bool                              = CACHE__DECORATOR__CONFIG__USE_CLASS_NAME   # Include class name in cache_key path
    use_method_name     : bool                              = CACHE__DECORATOR__CONFIG__USE_METHOD_NAME  # Include method name in cache_key path
    file_id             : str                               = CACHE__DECORATOR__CONFIG__FILE_ID          # Fixed file_id for stored responses
    cache_attr_name     : str                               = CACHE__DECORATOR__CONFIG__ATTRIBUTE_NAME   # Attribute name to look for cache client
    ttl_seconds         : Safe_UInt                         = None                                       # Time to live (None = no expiry, handled by cache service)
