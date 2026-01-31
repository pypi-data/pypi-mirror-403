"""
Cache configurations for Semantic Text Service.

This file contains pre-defined cache configurations for different services.
These configurations can be imported and used with the @cache_response decorator.
"""
from mgraph_ai_service_cache_client.client.decorator.schemas.Schema__Cache__Decorator__Config   import Schema__Cache__Decorator__Config
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Store__Strategy            import Enum__Cache__Store__Strategy

CACHE_CONFIG__TRANSFORMATION = Schema__Cache__Decorator__Config(
    namespace       = "cache-decorator__transformations"                           ,
    enabled         = True                                                      ,
    strategy        = Enum__Cache__Store__Strategy.KEY_BASED                    ,
    key_fields      = ["hash_mapping", "transformation_mode"]                   ,
    use_class_name  = True                                                      ,
    use_method_name = True                                                      ,
    file_id         = "response"                                                ,
)

# Cache configuration for Semantic Text Classification
CACHE_CONFIG__CLASSIFICATION = Schema__Cache__Decorator__Config(
    namespace       = "cache-decorator__classifications"                           ,
    enabled         = True                                                      ,
    strategy        = Enum__Cache__Store__Strategy.KEY_BASED                    ,
    key_fields      = ["text"]                                                  ,
    use_class_name  = True                                                      ,
    use_method_name = True                                                      ,
    file_id         = "classification"                                          ,
)

# Cache configuration for general purpose caching (minimal config)
CACHE_CONFIG__GENERAL = Schema__Cache__Decorator__Config(
    namespace       = "cache-decorator__general"                                   ,
    enabled         = True                                                      ,
    strategy        = Enum__Cache__Store__Strategy.KEY_BASED                    ,
    key_fields      = []                                                        ,  # Uses all params by default
    use_class_name  = True                                                      ,
    use_method_name = True                                                      ,
    file_id         = "response"                                                ,
)
