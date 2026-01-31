from fastapi                                                            import Path
from mgraph_ai_service_cache_client.schemas.cache.consts__Cache_Service import DEFAULT_CACHE__NAMESPACE, DEFAULT_CACHE__STORE__STRATEGY

FAST_API__PARAM__NAMESPACE                  = Path(..., example=DEFAULT_CACHE__NAMESPACE      , examples=[DEFAULT_CACHE__NAMESPACE      ])      # note: although we get a warning, examples is not currently working
FAST_API__PARAM__STRATEGY                   = Path(..., example=DEFAULT_CACHE__STORE__STRATEGY, examples=[DEFAULT_CACHE__STORE__STRATEGY])
# FAST_API__PARAM__NAMESPACE                  = Path(..., examples=[DEFAULT_CACHE__NAMESPACE      ])      # todo: see why this doesn't show the warning, but doesn't work (i.e. on the swagger we don't get the default value
# FAST_API__PARAM__STRATEGY                   = Path(..., examples=[DEFAULT_CACHE__STORE__STRATEGY])      #       where above it shows the warning, but doesn't work (see if this is a Fast_API or an FastAPI bug
ENV_VAR__CACHE__SERVICE__BUCKET_NAME        = 'CACHE__SERVICE__BUCKET_NAME'
ENV_VAR__CACHE__SERVICE__DEFAULT_TTL_HOURS  = 'CACHE__SERVICE__DEFAULT_TTL_HOURS'

DEFAULT__CACHE__SERVICE__BUCKET_NAME        = "mgraph-ai-cache"
DEFAULT__CACHE__SERVICE__DEFAULT_TTL_HOURS  = 24

CACHE__TEST__FIXTURES__BUCKET_NAME          = "test-cache-fixtures"
CACHE__TEST__FIXTURES__NAMESPACE            = "fixtures-namespace"


