# ═══════════════════════════════════════════════════════════════════════════════
# Cache Service Client - Data Operations Hub
# Central access point for data file operations under cache entries
# ═══════════════════════════════════════════════════════════════════════════════

from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client__Requests                import Cache__Service__Client__Requests
from mgraph_ai_service_cache_client.client.client_contract.data.Cache__Service__Client__Data__Delete    import Cache__Service__Client__Data__Delete
from mgraph_ai_service_cache_client.client.client_contract.data.Cache__Service__Client__Data__Exists    import Cache__Service__Client__Data__Exists
from mgraph_ai_service_cache_client.client.client_contract.data.Cache__Service__Client__Data__List      import Cache__Service__Client__Data__List
from mgraph_ai_service_cache_client.client.client_contract.data.Cache__Service__Client__Data__Retrieve  import Cache__Service__Client__Data__Retrieve
from mgraph_ai_service_cache_client.client.client_contract.data.Cache__Service__Client__Data__Update    import Cache__Service__Client__Data__Update
from osbot_utils.type_safe.Type_Safe                                                                    import Type_Safe
from osbot_utils.decorators.methods.cache_on_self                                                       import cache_on_self


class Cache__Service__Client__Data(Type_Safe):                                   # Hub for data file operations
    requests : Cache__Service__Client__Requests

    @cache_on_self
    def retrieve(self) -> Cache__Service__Client__Data__Retrieve:                # Access retrieve operations
        return Cache__Service__Client__Data__Retrieve(requests=self.requests)

    @cache_on_self
    def delete(self) -> Cache__Service__Client__Data__Delete:                    # Access delete operations
        return Cache__Service__Client__Data__Delete(requests=self.requests)

    @cache_on_self
    def exists(self) -> Cache__Service__Client__Data__Exists:                    # Access exists operations
        return Cache__Service__Client__Data__Exists(requests=self.requests)

    @cache_on_self
    def list(self) -> Cache__Service__Client__Data__List:                        # Access list operations
        return Cache__Service__Client__Data__List(requests=self.requests)

    @cache_on_self
    def update(self) -> Cache__Service__Client__Data__Update:                    # Access update operations
        return Cache__Service__Client__Data__Update(requests=self.requests)