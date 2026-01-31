# ═══════════════════════════════════════════════════════════════════════════════
# Cache__Service__Client
# Stateless facade for Cache service operations
# Config is stored in registry, looked up at request time
# ═══════════════════════════════════════════════════════════════════════════════
from osbot_utils.type_safe.Type_Safe                                                                    import Type_Safe
from osbot_utils.decorators.methods.cache_on_self                                                       import cache_on_self
from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client__Requests                import Cache__Service__Client__Requests
from mgraph_ai_service_cache_client.client.client_contract.admin.Cache__Service__Client__Admin__Storage import Cache__Service__Client__Admin__Storage
from mgraph_ai_service_cache_client.client.client_contract.data.Cache__Service__Client__Data            import Cache__Service__Client__Data
from mgraph_ai_service_cache_client.client.client_contract.data.Cache__Service__Client__Data__Store     import Cache__Service__Client__Data__Store
from mgraph_ai_service_cache_client.client.client_contract.file.Cache__Service__Client__File__Delete    import Cache__Service__Client__File__Delete
from mgraph_ai_service_cache_client.client.client_contract.file.Cache__Service__Client__File__Exists    import Cache__Service__Client__File__Exists
from mgraph_ai_service_cache_client.client.client_contract.file.Cache__Service__Client__File__Retrieve  import Cache__Service__Client__File__Retrieve
from mgraph_ai_service_cache_client.client.client_contract.file.Cache__Service__Client__File__Store     import Cache__Service__Client__File__Store
from mgraph_ai_service_cache_client.client.client_contract.file.Cache__Service__Client__File__Update    import Cache__Service__Client__File__Update
from mgraph_ai_service_cache_client.client.client_contract.info.Service__Fast_API__Client__Info         import Cache__Service__Client__Info
from mgraph_ai_service_cache_client.client.client_contract.namespace.Cache__Service__Client__Namespace  import Cache__Service__Client__Namespace
from mgraph_ai_service_cache_client.client.client_contract.namespace.Cache__Service__Client__Namespaces import Cache__Service__Client__Namespaces
from mgraph_ai_service_cache_client.client.client_contract.server.Cache__Service__Client__Server        import Cache__Service__Client__Server
from mgraph_ai_service_cache_client.client.client_contract.zip.Cache__Service__Client__Zip              import Cache__Service__Client__Zip


class Cache__Service__Client(Type_Safe):                                        # Stateless facade - config in registry

    @cache_on_self
    def requests(self) -> Cache__Service__Client__Requests:                     # Create transport with service_type set
        requests              = Cache__Service__Client__Requests()
        requests.service_type = Cache__Service__Client                          # Self-reference for registry lookup
        return requests

    def health(self) -> bool:                                                   # Health check
        try:
            result = self.info().health()
            return result.get('status') == 'ok'
        except:
            return False

    # ───────────────────────────────────────────────────────────────────────────
    # Domain Methods - Pass requests(), not self
    # ───────────────────────────────────────────────────────────────────────────

    @cache_on_self
    def store(self) -> Cache__Service__Client__File__Store:                            # Access store operations
        return Cache__Service__Client__File__Store(requests=self.requests())

    @cache_on_self
    def retrieve(self) -> Cache__Service__Client__File__Retrieve:                      # Access retrieve operations
        return Cache__Service__Client__File__Retrieve(requests=self.requests())

    @cache_on_self
    def exists(self) -> Cache__Service__Client__File__Exists:                          # Access exists operations
        return Cache__Service__Client__File__Exists(requests=self.requests())

    @cache_on_self
    def update(self) -> Cache__Service__Client__File__Update:                          # Access update operations
        return Cache__Service__Client__File__Update(requests=self.requests())

    @cache_on_self
    def delete(self) -> Cache__Service__Client__File__Delete:                          # Access delete operations
        return Cache__Service__Client__File__Delete(requests=self.requests())

    @cache_on_self
    def data_store(self) -> Cache__Service__Client__Data__Store:                       # Access data_store operations
        return Cache__Service__Client__Data__Store(requests=self.requests())

    @cache_on_self
    def data(self) -> Cache__Service__Client__Data:                                    # Access data operations
        return Cache__Service__Client__Data(requests=self.requests())

    @cache_on_self
    def zip(self) -> Cache__Service__Client__Zip:                                      # Access zip operations
        return Cache__Service__Client__Zip(requests=self.requests())

    @cache_on_self
    def namespace(self) -> Cache__Service__Client__Namespace:                          # Access namespace operations
        return Cache__Service__Client__Namespace(requests=self.requests())

    @cache_on_self
    def namespaces(self) -> Cache__Service__Client__Namespaces:                        # Access namespaces operations
        return Cache__Service__Client__Namespaces(requests=self.requests())

    @cache_on_self
    def admin_storage(self) -> Cache__Service__Client__Admin__Storage:                 # Access admin_storage operations
        return Cache__Service__Client__Admin__Storage(requests=self.requests())

    @cache_on_self
    def server(self) -> Cache__Service__Client__Server:                                # Access server operations
        return Cache__Service__Client__Server(requests=self.requests())

    @cache_on_self
    def info(self) -> Cache__Service__Client__Info:                                    # Access info operations
        return Cache__Service__Client__Info(requests=self.requests())
