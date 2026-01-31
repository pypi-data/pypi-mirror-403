# ═══════════════════════════════════════════════════════════════════════════════
# register_cache_service
# Registration helper for Cache service
# This file lives in mgraph_ai_service_cache (the heavy package)
# ═══════════════════════════════════════════════════════════════════════════════
from osbot_utils.utils.Env                                                                          import get_env
from osbot_fast_api.services.schemas.registry.safe_str.Safe_Str__Fast_API__Auth__Key_Name           import Safe_Str__Fast_API__Auth__Key_Name
from osbot_fast_api.services.schemas.registry.safe_str.Safe_Str__Fast_API__Auth__Key_Value          import Safe_Str__Fast_API__Auth__Key_Value
from osbot_fast_api_serverless.fast_api.Serverless__Fast_API__Config                                import Serverless__Fast_API__Config
from osbot_utils.type_safe.primitives.domains.web.safe_str.Safe_Str__Url                            import Safe_Str__Url
from osbot_utils.type_safe.type_safe_core.decorators.type_safe                                      import type_safe
from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client                      import Cache__Service__Client
from osbot_fast_api.services.registry.Fast_API__Service__Registry                                   import Fast_API__Service__Registry
from osbot_fast_api.services.registry.Fast_API__Service__Registry                                   import fast_api__service__registry
from osbot_fast_api.services.schemas.registry.Fast_API__Service__Registry__Client__Config           import Fast_API__Service__Registry__Client__Config
from osbot_fast_api.services.schemas.registry.enums.Enum__Fast_API__Service__Registry__Client__Mode import Enum__Fast_API__Service__Registry__Client__Mode
from mgraph_ai_service_cache.fast_api.Cache_Service__Fast_API                                       import Cache_Service__Fast_API
from mgraph_ai_service_cache_client.schemas.consts.consts__Cache_Client                             import ENV_VAR__AUTH__TARGET_SERVER__CACHE_SERVICE__KEY_NAME
from mgraph_ai_service_cache_client.schemas.consts.consts__Cache_Client                             import ENV_VAR__AUTH__TARGET_SERVER__CACHE_SERVICE__KEY_VALUE
from mgraph_ai_service_cache_client.schemas.consts.consts__Cache_Client                             import ENV_VAR__URL__TARGET_SERVER__CACHE_SERVICE

# todo see if these static methods should not be better in standalone files
def register_cache_service__in_memory(registry      : Fast_API__Service__Registry = None ,      # Register Cache service config for IN_MEMORY mode. Creates FastAPI app and registers config. Use for testing.
                                      return_client : bool                        = False,
                                 ) -> Cache__Service__Client:

    if registry is None:
        registry = fast_api__service__registry
    fast_api__config = Serverless__Fast_API__Config(enable_api_key=False)
    fast_api = Cache_Service__Fast_API(config=fast_api__config).setup()                                # Create FastAPI app
    
    config = Fast_API__Service__Registry__Client__Config(mode         = Enum__Fast_API__Service__Registry__Client__Mode.IN_MEMORY,
                                                         fast_api     = fast_api      ,
                                                         fast_api_app = fast_api.app())
    
    registry.register(Cache__Service__Client, config)
    if return_client:
        return Cache__Service__Client()
    return None


@type_safe
def register_cache_service__remote(registry      : Fast_API__Service__Registry          = None,
                                   base_url      : Safe_Str__Url                        = None,
                                   api_key_name  : Safe_Str__Fast_API__Auth__Key_Name   = None,
                                   api_key_value : Safe_Str__Fast_API__Auth__Key_Value  = None
                                  ) -> Fast_API__Service__Registry__Client__Config:
    """Register Cache service config for REMOTE mode.
    
    If credentials not provided, reads from environment variables.
    Use for production.
    """
    if registry is None:
        registry = fast_api__service__registry
        
    # Use provided values or fall back to env vars
    url   = base_url      or get_env(ENV_VAR__URL__TARGET_SERVER__CACHE_SERVICE            )
    name  = api_key_name  or get_env(ENV_VAR__AUTH__TARGET_SERVER__CACHE_SERVICE__KEY_NAME )
    value = api_key_value or get_env(ENV_VAR__AUTH__TARGET_SERVER__CACHE_SERVICE__KEY_VALUE)
    
    if not url:
        raise ValueError(f"REMOTE mode requires base_url or {ENV_VAR__URL__TARGET_SERVER__CACHE_SERVICE} env var")
    
    config = Fast_API__Service__Registry__Client__Config(
        mode          = Enum__Fast_API__Service__Registry__Client__Mode.REMOTE,
        base_url      = url  ,
        api_key_name  = name ,
        api_key_value = value
    )
    
    registry.register(Cache__Service__Client, config)
    return config


def register_cache_service__from_env(registry: Fast_API__Service__Registry = None
                                    ) -> None:
    """Register Cache service config based on environment.
    
    If CACHE_SERVICE_URL is set, uses REMOTE mode.
    Otherwise, uses IN_MEMORY mode (for testing).
    """
    if registry is None:
        registry = fast_api__service__registry
        
    target_url = get_env(ENV_VAR__URL__TARGET_SERVER__CACHE_SERVICE)
    
    if target_url:
        register_cache_service__remote(registry=registry)
    else:
        register_cache_service__in_memory(registry=registry)
