# ═══════════════════════════════════════════════════════════════════════════════
# Cache__Entity - Bound client for cache entity operations
# Wraps cache_id + namespace to provide simplified access to all entity operations
#
# Usage:
#   entity = Cache__Entity(cache_client=client, cache_id=id, namespace=ns)
#   entry  = entity.entry()           # Get entry data
#   refs   = entity.refs()            # Get file references
#   html   = entity.data__string('html', 'raw')  # Get data file
#
#   # Or go one level deeper:
#   data_file = entity.data_file('html', 'raw')
#   html      = data_file.string()
# ═══════════════════════════════════════════════════════════════════════════════
from typing import List

from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client import Cache__Service__Client
from mgraph_ai_service_cache_client.client.client_entities.Cache__Entity__Data_File          import Cache__Entity__Data_File
from mgraph_ai_service_cache_client.schemas.cache.Schema__Cache__Retrieve__Success           import Schema__Cache__Retrieve__Success
from mgraph_ai_service_cache_client.schemas.cache.data.Schema__Cache__Data__List__Response   import Schema__Cache__Data__List__Response
from mgraph_ai_service_cache_client.schemas.cache.data.Schema__Cache__Data__Store__Response  import Schema__Cache__Data__Store__Response
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Data_Type               import Enum__Cache__Data_Type
from mgraph_ai_service_cache_client.schemas.cache.file.Schema__Cache__File__Metadata         import Schema__Cache__File__Metadata
from mgraph_ai_service_cache_client.schemas.cache.file.Schema__Cache__File__Refs             import Schema__Cache__File__Refs
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__Cache_Hash import Safe_Str__Cache__File__Cache_Hash
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__Data_Key   import Safe_Str__Cache__File__Data_Key
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__File_Id    import Safe_Str__Cache__File__File_Id
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__Namespace        import Safe_Str__Cache__Namespace
from osbot_utils.testing.__                                                                  import __
from osbot_utils.testing.__helpers                                                           import obj
from osbot_utils.type_safe.Type_Safe                                                         import Type_Safe
from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path            import Safe_Str__File__Path
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                           import Cache_Id
from osbot_utils.type_safe.type_safe_core.decorators.type_safe                               import type_safe


class Cache__Entity(Type_Safe):                                                             # Bound client for entity operations
    cache_client : Cache__Service__Client                                                   # Cache service client
    cache_id     : Cache_Id                                                                 # Entity cache_id
    namespace    : Safe_Str__Cache__Namespace                                               # Cache namespace

    # ═══════════════════════════════════════════════════════════════════════════
    # Entry Operations (Tier 1 - the root entity)
    # ═══════════════════════════════════════════════════════════════════════════

    # todo: see if we need to add support for entry__binary and entry__text/entry__string

    @type_safe
    def entry__json(self) -> dict:                                                                # Get entry data as dict
        return self.cache_client.retrieve().retrieve__cache_id__json(cache_id  = self.cache_id ,
                                                                     namespace = self.namespace)

    def entry__json__obj(self) -> __:                                                                # Get entry data as dict
        return obj(self.entry__json())

    @type_safe
    def entry__with_metadata(self) -> Schema__Cache__Retrieve__Success:                            # Get full entry with metadata
        return self.cache_client.retrieve().retrieve__cache_id(cache_id  = self.cache_id ,
                                                               namespace = self.namespace)

    @type_safe
    def metadata(self) -> Schema__Cache__File__Metadata:                                    # Get entry metadata
        return self.cache_client.retrieve().retrieve__cache_id__metadata(cache_id  = self.cache_id ,
                                                                         namespace = self.namespace)

    @type_safe
    def refs(self) -> Schema__Cache__File__Refs:                                            # Get all file references
        return self.cache_client.retrieve().retrieve__cache_id__refs(cache_id  = self.cache_id ,
                                                                     namespace = self.namespace)

    @type_safe
    def exists(self) -> bool:                                                               # Check if entity exists
        response = self.cache_client.exists().exists__cache_id(cache_id  = self.cache_id ,
                                                               namespace = self.namespace)
        if response:
            return response.exists
        return False

    @type_safe
    def delete(self) -> bool:                                                               # Delete the entity
        response = self.cache_client.delete().delete__cache_id(cache_id  = self.cache_id ,
                                                               namespace = self.namespace)
        if response:
            return response.get('status') == 'success'
        return False

    # ═══════════════════════════════════════════════════════════════════════════
    # Data Operations (Tier 2 - data files attached to entity)
    # ═══════════════════════════════════════════════════════════════════════════

    @type_safe
    def data__files(self                              ,                                     # List all data files
                    data_key  : str  = None           ,                                     # Optional path filter
                    recursive : bool = True
               ) -> Schema__Cache__Data__List__Response:
        if data_key:
            return self.cache_client.data().list().data__list__with__key(cache_id  = self.cache_id ,
                                                                         namespace = self.namespace,
                                                                         data_key  = data_key     ,
                                                                         recursive = recursive    )
        return self.cache_client.data().list().data__list(cache_id  = self.cache_id ,
                                                          namespace = self.namespace,
                                                          recursive = recursive    )
    @type_safe
    def data__files__paths(self) -> List[Safe_Str__File__Path]:
        return [file.file_path for file in self.data__files().files]

    @type_safe
    def data__string(self                   ,                                               # Get data file as string
                     data_key     : str     ,
                     data_file_id : str
                ) -> str:
        response = self.cache_client.data().retrieve().data__string__with__id_and_key(cache_id     = self.cache_id ,
                                                                                      namespace    = self.namespace,
                                                                                      data_key     = data_key      ,
                                                                                      data_file_id = data_file_id  )
        if type(response) is dict:                                                          # Handle error response
            return None
        if response:
            return response
        return None

    @type_safe
    def data__json(self                   ,                                                 # Get data file as JSON
                   data_key     : str     ,
                   data_file_id : str
              ) -> dict:
        return self.cache_client.data().retrieve().data__json__with__id_and_key(cache_id     = self.cache_id ,
                                                                                namespace    = self.namespace,
                                                                                data_key     = data_key      ,
                                                                                data_file_id = data_file_id  )

    @type_safe
    def data__exists(self                                          ,                        # Check if data file exists
                     data_key     : str                            ,
                     data_file_id : str                            ,
                     data_type    : Enum__Cache__Data_Type = Enum__Cache__Data_Type.STRING
                ) -> bool:
        result = self.cache_client.data().exists().data__exists__with__id_and_key(cache_id     = self.cache_id ,
                                                                                  namespace    = self.namespace,
                                                                                  data_key     = data_key      ,
                                                                                  data_file_id = data_file_id  ,
                                                                                  data_type    = data_type     )
        if result:
            return result.exists
        return False

    @type_safe
    def data__store_string(self                   ,                                         # Store string data file
                           data_key     : str     ,
                           data_file_id : str     ,
                           content      : str
                      ) -> Schema__Cache__Data__Store__Response:
        return self.cache_client.data_store().data__store_string__with__id_and_key(cache_id     = self.cache_id ,
                                                                                   namespace    = self.namespace,
                                                                                   data_key     = data_key      ,
                                                                                   data_file_id = data_file_id  ,
                                                                                   body         = content       )

    @type_safe
    def data__store_json(self                   ,                                           # Store JSON data file
                         data_key     : Safe_Str__Cache__File__Data_Key ,
                         data_file_id : Safe_Str__Cache__File__File_Id  ,
                         data         : dict
                    ) -> Schema__Cache__Data__Store__Response:
        return self.cache_client.data_store().data__store_json__with__id_and_key(cache_id     = self.cache_id ,
                                                                                 namespace    = self.namespace,
                                                                                 data_key     = data_key      ,
                                                                                 data_file_id = data_file_id  ,
                                                                                 body         = data          )

    @type_safe
    def data__update_string(self                   ,                                        # Update string data file
                            data_key     : str     ,
                            data_file_id : str     ,
                            content      : str
                       ) -> bool:
        result = self.cache_client.data().update().data__update_string__with__id_and_key(cache_id     = self.cache_id ,
                                                                                         namespace    = self.namespace,
                                                                                         data_key     = data_key      ,
                                                                                         data_file_id = data_file_id  ,
                                                                                         body         = content       )
        if result:
            return result.success
        return False

    @type_safe
    def data__update_json(self                   ,                                          # Update JSON data file
                          data_key     : str     ,
                          data_file_id : str     ,
                          data         : dict
                     ) -> bool:
        result = self.cache_client.data().update().data__update_json__with__id_and_key(cache_id     = self.cache_id ,
                                                                                       namespace    = self.namespace,
                                                                                       data_key     = data_key      ,
                                                                                       data_file_id = data_file_id  ,
                                                                                       body         = data          )
        if result:
            return result.success
        return False

    @type_safe
    def data__delete(self                                          ,                        # Delete data file
                     data_key     : str                            ,
                     data_file_id : str                            ,
                     data_type    : Enum__Cache__Data_Type = Enum__Cache__Data_Type.STRING
                ) -> bool:
        result = self.cache_client.data().delete().delete__data__file__with__id_and_key(cache_id     = self.cache_id ,
                                                                                        namespace    = self.namespace,
                                                                                        data_key     = data_key      ,
                                                                                        data_file_id = data_file_id  ,
                                                                                        data_type    = data_type     )
        if result:
            return result.get('status') == 'success'
        return False

    # ═══════════════════════════════════════════════════════════════════════════
    # Factory Methods
    # ═══════════════════════════════════════════════════════════════════════════

    def data_file(self                   ,                                                  # Create bound data file client
                  data_key     : str     ,
                  data_file_id : str
             ) -> Cache__Entity__Data_File:

        return Cache__Entity__Data_File(cache_client = self.cache_client,
                                        cache_id     = self.cache_id    ,
                                        namespace    = self.namespace   ,
                                        data_key     = data_key         ,
                                        data_file_id = data_file_id     )

    # ═══════════════════════════════════════════════════════════════════════════
    # Cache Operations (direct access to cache raw files)
    # ═══════════════════════════════════════════════════════════════════════════

    @type_safe
    def cache__hash(self) -> Safe_Str__Cache__File__Cache_Hash:                             # Get the cache has from the refs file
        refs       = self.refs()
        if refs:
            return refs.cache_hash
        else:
            return None

    @type_safe
    def cache__file__hash(self) -> dict:                                                    # get the contents of the hash value for this cache_id
        cache_hash = self.cache__hash()
        return self.cache_client.retrieve().retrieve__hash__cache_hash__refs_hash(cache_hash = cache_hash    ,
                                                                                  namespace  = self.namespace)
    def cache__file__hash__obj(self) -> __:
        return obj(self.cache__file__hash())