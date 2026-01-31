# ═══════════════════════════════════════════════════════════════════════════════
# Cache__Service__Client__Requests
# Transport layer for Cache service - extends generic Fast_API__Client__Requests
# ═══════════════════════════════════════════════════════════════════════════════

from osbot_fast_api.services.registry.Fast_API__Client__Requests                import Fast_API__Client__Requests


class Cache__Service__Client__Requests(Fast_API__Client__Requests):             # Cache-specific transport
    pass                                                                        # service_type set at runtime by Cache__Service__Client
