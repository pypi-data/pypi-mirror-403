"""
Cache Client Test Helpers

Provides helper methods to create test state using ONLY client API methods.
No direct access to cache_service internals - tests the complete client contract.

Usage:
    helpers = Cache_Client_Test_Helpers(client=cache_service_client)
    entry = helpers.create_string_entry(namespace="test", value="data")
    assert helpers.verify_entry_exists(entry['cache_id'], "test")
"""

from typing                                                                                      import Dict, List, Tuple
from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client                   import Cache__Service__Client
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                               import Cache_Id
from osbot_utils.utils.Misc                                                                      import random_string, random_bytes, str_to_bytes
from osbot_utils.type_safe.Type_Safe                                                             import Type_Safe
from osbot_utils.type_safe.type_safe_core.decorators.type_safe                                   import type_safe
from mgraph_ai_service_cache_client.schemas.cache.Schema__Cache__Store__Response                 import Schema__Cache__Store__Response
from mgraph_ai_service_cache_client.schemas.cache.data.Schema__Cache__Data__Store__Response      import Schema__Cache__Data__Store__Response
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Store__Strategy             import Enum__Cache__Store__Strategy


class Cache_Client_Test_Helpers(Type_Safe):         # Helper methods to create and verify test state using only client API

    cache_service_client: Cache__Service__Client

    # ═══════════════════════════════════════════════════════════════════════════════
    # Store Operations - Create test entries
    # ═══════════════════════════════════════════════════════════════════════════════

    @type_safe
    def create_string_entry(self,
                           namespace : str                            = 'test'                         ,
                           value     : str                            = None                           ,
                           strategy  : Enum__Cache__Store__Strategy   = Enum__Cache__Store__Strategy.DIRECT,
                           cache_key : str                            = None                           ,
                           file_id   : str                            = None
                      ) -> Schema__Cache__Store__Response:
        if value is None:
            value = random_string('test_value_')

        with self.cache_service_client.store() as _:
            if cache_key or file_id:
                return _.store__string__cache_key(namespace  = namespace  ,
                                                  strategy   = strategy   ,
                                                  cache_key  = cache_key or 'test/key',
                                                  body       = value      ,
                                                  file_id    = file_id or '')
            else:
                return _.store__string(strategy  = strategy  ,
                                       namespace = namespace ,
                                       body      = value     )

    @type_safe
    def create_json_entry(self,
                         namespace : str                            = 'test'                         ,
                         data      : dict                           = None                           ,
                         strategy  : Enum__Cache__Store__Strategy   = Enum__Cache__Store__Strategy.DIRECT,
                         cache_key : str                            = None                           ,
                         file_id   : str                            = None
                    ) -> Schema__Cache__Store__Response:
        """
        Create a JSON cache entry and return full result
        """
        if data is None:
            data = {'test': 'data', 'random': random_string()}

        with self.cache_service_client.store() as _:
            if cache_key or file_id:
                return _.store__json__cache_key(namespace  = namespace  ,
                                               strategy   = strategy   ,
                                               cache_key  = cache_key or 'test/key',
                                               body       = data       ,
                                               file_id    = file_id or '')
            else:
                return _.store__json(strategy  = strategy  ,
                                    namespace = namespace ,
                                    body      = data      )

    @type_safe
    def create_binary_entry(self,
                           namespace : str                            = 'test'                         ,
                           data      : bytes                          = None                           ,
                           strategy  : Enum__Cache__Store__Strategy   = Enum__Cache__Store__Strategy.DIRECT,
                           cache_key : str                            = None                           ,
                           file_id   : str                            = None
                      ) -> Schema__Cache__Store__Response:
        """
        Create a binary cache entry and return full result
        """
        if data is None:
            data = random_bytes()

        with self.cache_service_client.store() as _:
            if cache_key or file_id:
                return _.store__binary__cache_key(namespace  = namespace  ,
                                                  strategy   = strategy   ,
                                                  cache_key  = cache_key or 'test/key',
                                                  body       = data       ,
                                                  file_id    = file_id or '')
            else:
                return _.store__binary(strategy  = strategy  ,
                                       namespace = namespace ,
                                       body      = data      )

    # ═══════════════════════════════════════════════════════════════════════════════
    # Data File Operations - Create child data files
    # ═══════════════════════════════════════════════════════════════════════════════

    @type_safe
    def add_data_string(self,
                       cache_id     : str  ,
                       namespace    : str  = 'test',
                       data         : str  = None  ,
                       data_file_id : str  = None  ,
                       data_key     : str  = None
                  ) -> Schema__Cache__Data__Store__Response:
        """
        Add a string data file to existing cache entry

        Returns: Schema__Cache__Data__Store__Response dict
        """
        if data is None:
            data = random_string('data_value_')

        with self.cache_service_client.data_store() as _:
            if data_key and data_file_id:
                return _.data__store_string__with__id_and_key(cache_id     = cache_id     ,
                                                              namespace    = namespace    ,
                                                              data_key     = data_key     ,
                                                              data_file_id = data_file_id ,
                                                              body         = data         )
            elif data_file_id:
                return _.data__store_string__with__id(cache_id     = cache_id     ,
                                                      namespace    = namespace    ,
                                                      data_file_id = data_file_id ,
                                                      body         = data         )
            else:
                return _.data__store_string(cache_id  = cache_id  ,
                                           namespace = namespace ,
                                           body      = data      )

    @type_safe
    def add_data_json(self,
                     cache_id     : str  ,
                     namespace    : str  = 'test',
                     data         : dict = None  ,
                     data_file_id : str  = None  ,
                     data_key     : str  = None
                ) -> Schema__Cache__Data__Store__Response:
        """
        Add a JSON data file to existing cache entry
        """
        if data is None:
            data = {'data': 'value', 'random': random_string()}

        with self.cache_service_client.data_store() as _:
            if data_key and data_file_id:
                return _.data__store_json__with__id_and_key(cache_id     = cache_id     ,
                                                            namespace    = namespace    ,
                                                            data_key     = data_key     ,
                                                            data_file_id = data_file_id ,
                                                            body         = data         )
            elif data_file_id:
                return _.data__store_json__with__id(cache_id     = cache_id     ,
                                                    namespace    = namespace    ,
                                                    data_file_id = data_file_id ,
                                                    body         = data         )
            else:
                return _.data__store_json(cache_id  = cache_id  ,
                                         namespace = namespace ,
                                         body      = data      )

    @type_safe
    def add_data_binary(self,
                       cache_id     : str   ,
                       namespace    : str   = 'test',
                       data         : bytes = None  ,
                       data_file_id : str   = None  ,
                       data_key     : str   = None
                  ) -> Schema__Cache__Data__Store__Response:
        """
        Add a binary data file to existing cache entry
        """
        if data is None:
            data = random_bytes()

        with self.cache_service_client.data_store() as _:
            if data_key and data_file_id:
                return _.data__store_binary__with__id_and_key(cache_id     = cache_id     ,
                                                              namespace    = namespace    ,
                                                              data_key     = data_key     ,
                                                              data_file_id = data_file_id ,
                                                              body         = data         )
            elif data_file_id:
                return _.data__store_binary__with__id(cache_id     = cache_id     ,
                                                      namespace    = namespace    ,
                                                      data_file_id = data_file_id ,
                                                      body         = data         )
            else:
                return _.data__store_binary(cache_id  = cache_id  ,
                                            namespace = namespace ,
                                            body      = data      )

    @type_safe
    def create_entry_with_data_files(self,
                                    namespace      : str = 'test',
                                    string_count   : int = 2    ,
                                    json_count     : int = 2    ,
                                    binary_count   : int = 1    ,
                                    use_data_keys  : bool = False
                               ) -> Tuple[Cache_Id, Schema__Cache__Store__Response, List[str]]:
        """
        Create a cache entry with multiple data files attached

        Returns: (cache_id, store_result)
        """
        # Create main entry
        store_result = self.create_string_entry(namespace = namespace ,
                                                value     = 'main_entry')
        cache_id = store_result.cache_id

        # Add string data files
        for i in range(string_count):
            data_file_id = f'string-data-{i}'
            data_key     = f'strings/data-{i}' if use_data_keys else None
            self.add_data_string(cache_id     = cache_id     ,
                                 namespace    = namespace    ,
                                 data_file_id = data_file_id ,
                                 data_key     = data_key     )

        # Add JSON data files
        for i in range(json_count):
            data_file_id = f'json-data-{i}'
            data_key     = f'jsons/data-{i}' if use_data_keys else None
            self.add_data_json(cache_id     = cache_id     ,
                               namespace    = namespace    ,
                               data_file_id = data_file_id ,
                               data_key     = data_key     )

        # Add binary data files
        for i in range(binary_count):
            data_file_id = f'binary-data-{i}'
            data_key     = f'binaries/data-{i}' if use_data_keys else None
            self.add_data_binary(cache_id     = cache_id     ,
                                 namespace    = namespace    ,
                                 data_file_id = data_file_id ,
                                 data_key     = data_key     )

        files__in_cache_id = self.admin__get_files_in_folder__by_cache_id__direct(namespace=namespace, cache_id=cache_id)
        return cache_id, store_result, files__in_cache_id

    # ═══════════════════════════════════════════════════════════════════════════════
    # Verification Methods - Check state using client API
    # ═══════════════════════════════════════════════════════════════════════════════

    @type_safe
    def verify_entry_exists(self,
                           cache_id  : str ,
                           namespace : str = 'test'
                      ) -> bool:
        """
        Verify cache entry exists by trying to retrieve it
        Returns True if exists, False otherwise
        """
        with self.cache_service_client.retrieve() as _:
            result = _.retrieve__cache_id(cache_id  = cache_id  ,
                                         namespace = namespace )
            return result is not None

    @type_safe
    def verify_entry_exists_by_hash(self,
                                   cache_hash : str ,
                                   namespace  : str = 'test'
                              ) -> bool:
        """
        Verify cache entry exists by hash
        """
        with self.cache_service_client.retrieve() as _:
            result = _.retrieve__hash__cache_hash(cache_hash = cache_hash ,
                                                 namespace  = namespace  )
            return result is not None

    @type_safe
    def verify_data_file_exists(self,
                               cache_id     : str ,
                               data_file_id : str ,
                               namespace    : str = 'test',
                               data_key     : str = None
                          ) -> bool:
        """
        Verify data file exists by trying to retrieve it
        """

        with self.cache_service_client.data().retrieve() as _:
            if data_key:
                result = _.data__string__with__id_and_key(cache_id     = cache_id     ,
                                                          namespace    = namespace    ,
                                                          data_key     = data_key     ,
                                                          data_file_id = data_file_id )
            else:
                result = _.data__string__with__id(cache_id     = cache_id     ,
                                                  namespace    = namespace    ,
                                                  data_file_id = data_file_id )
            return result is not None

    @type_safe
    def get_namespace_file_count(self, namespace: str = 'test') -> int:
        """
        Get total file count in namespace using admin API
        Returns file count or 0 if namespace doesn't exist

        NOTE: Uses admin_storage() which might not be available in production
        """

        with self.cache_service_client.admin_storage() as _:
            result = _.files__all__path(path = namespace)
            return result.file_count if result else 0

    @type_safe
    def get_all_namespaces(self) -> List[str]:
        """
        Get list of all namespaces
        Returns empty list if none exist
        """
        try:
            with self.cache_service_client.namespaces() as _:
                return _.list()
        except:
            return []

    # ═══════════════════════════════════════════════════════════════════════════════
    # Complex Test Scenarios - Multi-step operations
    # ═══════════════════════════════════════════════════════════════════════════════

    @type_safe
    def create_multi_strategy_entries(self,
                                     namespace : str = 'test'
                                ) -> Dict[str, Schema__Cache__Store__Response]:
        """
        Create entries using all storage strategies

        Returns: {
            'direct': {...},
            'temporal': {...},
            'temporal_latest': {...},
            'temporal_versioned': {...},
            'key_based': {...}
        }
        """
        strategies = [  Enum__Cache__Store__Strategy.DIRECT             ,
                        Enum__Cache__Store__Strategy.TEMPORAL           ,
                        Enum__Cache__Store__Strategy.TEMPORAL_LATEST    ,
                        Enum__Cache__Store__Strategy.TEMPORAL_VERSIONED ,
                        Enum__Cache__Store__Strategy.KEY_BASED          ]

        results = {}
        for strategy in strategies:
            result = self.create_string_entry(namespace = namespace                  ,
                                             value     = f'test_{strategy.value}'   ,
                                             strategy  = strategy                   )
            results[strategy.value] = result

        return results

    @type_safe
    def create_versioned_entries(self,
                                namespace   : str = 'test'      ,
                                cache_key   : str = 'test/key'  ,
                                version_count: int = 3
                           ) -> List[Schema__Cache__Store__Response]:
        """
        Create multiple versions of same cache_key using TEMPORAL_VERSIONED

        Returns: List of store results, one per version
        """
        results = []
        strategy = Enum__Cache__Store__Strategy.TEMPORAL_VERSIONED

        for i in range(version_count):
            result = self.create_string_entry(namespace = namespace           ,
                                             value     = f'version_{i}'      ,
                                             strategy  = strategy            ,
                                             cache_key = cache_key           )
            results.append(result)

        return results

    @type_safe
    def create_namespace_hierarchy(self,
                                  base_namespace : str = 'test',
                                  depth          : int = 3     ,
                                  entries_per_ns : int = 2
                             ) -> Dict[str, List[Schema__Cache__Store__Response]]:
        """
        Create nested namespace structure with entries

        Example: 'test', 'test-level1', 'test-level2', etc.

        Returns: {'namespace': [entry1, entry2, ...], ...}
        """
        results = {}

        for level in range(depth):
            namespace = f"{base_namespace}-level{level}" if level > 0 else base_namespace
            entries = []

            for i in range(entries_per_ns):
                entry = self.create_string_entry(namespace = namespace           ,
                                                value     = f'entry_{level}_{i}')
                entries.append(entry)

            results[namespace] = entries

        return results

    # ═══════════════════════════════════════════════════════════════════════════════
    # Cleanup Operations
    # ═══════════════════════════════════════════════════════════════════════════════

    # todo: refactor to add type safe return type
    @type_safe
    def delete_entry(self,
                    cache_id  : str ,
                    namespace : str = 'test'
               ) -> Dict:
        """
        Delete a cache entry

        Returns: Delete result dict
        """
        with self.cache_service_client.delete() as _:
            return _.delete__cache_id(cache_id  = cache_id  ,
                                      namespace = namespace )

    @type_safe
    def delete_all_data_files(self,
                             cache_id  : str ,
                             namespace : str = 'test'
                        ) -> Dict:
        """
        Delete all data files for a cache entry

        Returns: Delete result dict
        """
        with self.cache_service_client.data().delete() as _:
            return _.delete__all__data__files(cache_id  = cache_id  ,
                                             namespace = namespace )

    # ═══════════════════════════════════════════════════════════════════════════════
    # Path Building Helpers - Expected Path Generation
    # ═══════════════════════════════════════════════════════════════════════════════

    @type_safe
    def build_expected_paths(self,
                             cache_id   : str                            ,
                             cache_hash : str                            ,
                             namespace  : str                = 'test'    ,
                             strategy   : Enum__Cache__Store__Strategy   = Enum__Cache__Store__Strategy.DIRECT,
                             file_id    : str                            = None    ,
                             cache_key  : str                            = None    ,
                             extension  : str                            = 'json'
                        ) -> Dict[str, list]:

        from datetime import datetime

        cache_id_prefix = f"{cache_id[0:2]}/{cache_id[2:4]}"
        hash_prefix     = f"{cache_hash[0:2]}/{cache_hash[2:4]}"
        if file_id:
            file_id_prefix  = f"{file_id[0:2]}/{file_id[2:4]}"
        else:
            file_id_prefix = ""

        # Determine file identifier
        file_name = file_id if file_id else cache_id

        # Build data path based on strategy
        data_files = []

        if strategy == Enum__Cache__Store__Strategy.DIRECT:
            if cache_key and file_id:
                data_base = f"{namespace}/data/direct/{cache_key}/{file_id}.{extension}"
            elif file_id:
                data_base = f"{namespace}/data/direct/{file_id_prefix}/{file_id}.{extension}"
            else:
                data_base = f"{namespace}/data/direct/{cache_id_prefix}/{cache_id}.{extension}"
            data_files = [data_base, f"{data_base}.config", f"{data_base}.metadata"]

        elif strategy == Enum__Cache__Store__Strategy.TEMPORAL:
            now = datetime.now()
            temporal_path = f"{now.year}/{now.month:02d}/{now.day:02d}/{now.hour:02d}"
            data_base = f"{namespace}/data/temporal/{temporal_path}/{file_name}.{extension}"
            data_files = [data_base, f"{data_base}.config", f"{data_base}.metadata"]

        elif strategy == Enum__Cache__Store__Strategy.TEMPORAL_LATEST:
            now = datetime.now()
            temporal_path = f"{now.year}/{now.month:02d}/{now.day:02d}/{now.hour:02d}"
            # Two sets of files: versioned + latest
            versioned_base = f"{namespace}/data/temporal-latest/{temporal_path}/{file_name}.{extension}"
            latest_base    = f"{namespace}/data/temporal-latest/latest/{file_name}.{extension}"
            data_files = [
                versioned_base, f"{versioned_base}.config", f"{versioned_base}.metadata",
                latest_base,    f"{latest_base}.config",    f"{latest_base}.metadata"
            ]

        elif strategy == Enum__Cache__Store__Strategy.TEMPORAL_VERSIONED:
            now = datetime.now()
            temporal_path = f"{now.year}/{now.month:02d}/{now.day:02d}/{now.hour:02d}"
            # Three sets of files: temporal + latest + version
            temporal_base = f"{namespace}/data/temporal-versioned/{temporal_path}/{file_name}.{extension}"
            latest_base   = f"{namespace}/data/temporal-versioned/latest/{file_name}.{extension}"
            version_base  = f"{namespace}/data/temporal-versioned/versions/v1/{file_name}.{extension}"
            data_files = [
                temporal_base, f"{temporal_base}.config", f"{temporal_base}.metadata",
                latest_base,   f"{latest_base}.config",   f"{latest_base}.metadata",
                version_base,  f"{version_base}.config",  f"{version_base}.metadata"
            ]

        elif strategy == Enum__Cache__Store__Strategy.KEY_BASED:
            if cache_key and file_id:
                data_base = f"{namespace}/data/key-based/{cache_key}/{file_id}.{extension}"
            elif cache_key:
                data_base = f"{namespace}/data/key-based/{cache_key}/{cache_id}.{extension}"
            elif file_id:
                data_base = f"{namespace}/data/key-based/{cache_id_prefix}/{file_id}.{extension}"
            else:
                data_base = f"{namespace}/data/key-based/{cache_id}.{extension}"
            data_files = [data_base, f"{data_base}.config", f"{data_base}.metadata"]

        else:
            raise Exception(f"Strategy {strategy} is not supported.")
            # # Fallback to direct if unknown strategy
            # data_base = f"{namespace}/data/{strategy.value}/{cache_id_prefix}/{cache_id}.{extension}"
            # data_files = [data_base, f"{data_base}.config", f"{data_base}.metadata"]

        return { 'data'    : data_files,
                 'by_hash' : [f"{namespace}/refs/by-hash/{hash_prefix}/{cache_hash}.json" ],
                 'by_id'   : [f"{namespace}/refs/by-id/{cache_id_prefix}/{cache_id}.json" ]}

    # @type_safe
    # def build_expected_store_result(self,
    #                                 cache_id   : str                            ,
    #                                 cache_hash : str                            ,
    #                                 namespace  : str                = 'test'    ,
    #                                 strategy   : Enum__Cache__Store__Strategy   = Enum__Cache__Store__Strategy.DIRECT,
    #                                 size       : int                            = None  ,
    #                                 file_id    : str                            = None  ,
    #                                 cache_key  : str                            = None  ,
    #                                 extension  : str                            = 'json'
    #                            ) -> Dict:
    #     paths = self.build_expected_paths(cache_id   = cache_id   ,
    #                                       cache_hash = cache_hash ,
    #                                       namespace  = namespace  ,
    #                                       strategy   = strategy   ,
    #                                       file_id    = file_id    ,
    #                                       cache_key  = cache_key  ,
    #                                       extension  = extension  )
    #
    #     result = { 'cache_id'   : cache_id   ,
    #                'cache_hash' : cache_hash ,
    #                'namespace'  : namespace  ,
    #                'paths'      : paths      }
    #
    #     if size is not None:
    #         result['size'] = size
    #
    #     return result

    # Admin storage helpers
    # todo: add missing type_safety return type (needs fix to in cache service code)
    def admin__get_files_in_folder__by_cache_id__direct(self, namespace, cache_id):
        path            = f'{namespace}/data/direct/{cache_id[0:2]}/{cache_id[2:4]}/'                          # Verify data files created
        recursive       = True
        files_full_path = self.cache_service_client.admin_storage().files__in__path(path      = path,
                                                                                    recursive = recursive)
        files           = []
        for file_full_path in files_full_path:
            files.append(file_full_path.replace(path, ""))
        return files

# ═══════════════════════════════════════════════════════════════════════════════════
# Gaps/Missing Client Methods to Address Later
# ═══════════════════════════════════════════════════════════════════════════════════
"""
GAPS IDENTIFIED:

1. No client method to list all entries in a namespace
   - Would need: client.namespace().list_entries() or similar
   - Workaround: Use admin_storage().files__in__path() but that's admin-only

2. No client method to get data file list for a cache entry
   - Would need: client.data().list(cache_id, namespace)
   - Currently must use admin_storage() to inspect data folder

3. No client method to verify data file exists without retrieving it
   - Would need: client.data().exists(cache_id, data_file_id, namespace)
   - Currently must try to retrieve and catch errors

4. No client method to get cache entry metadata without content
   - Have: retrieve__cache_id__metadata() - but returns all metadata
   - Would be useful: get_size(), get_timestamps(), etc.

5. No batch delete operations
   - Would need: client.delete().delete_multiple([cache_ids], namespace)
   - Currently must delete one by one

6. No namespace statistics via client (only admin)
   - Would need: client.namespace().stats(namespace)
   - Currently only: admin_storage() can get stats

7. Limited data file filtering
   - No way to list data files by type (string/json/binary)
   - No way to list data files matching a pattern
"""