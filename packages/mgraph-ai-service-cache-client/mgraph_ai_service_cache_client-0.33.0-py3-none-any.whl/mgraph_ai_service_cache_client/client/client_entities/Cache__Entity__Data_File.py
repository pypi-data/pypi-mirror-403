# ═══════════════════════════════════════════════════════════════════════════════
# Cache__Data__File - Bound client for data file operations
# Wraps cache_id + namespace + data_key + data_file_id for simplified access
#
# Usage:
#   data_file = Cache__Data__File(cache_client=client, cache_id=id, namespace=ns,
#                                  data_key='html', data_file_id='raw')
#   content = data_file.string()           # Get content
#   data_file.store_string(html)           # Store content
from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client import Cache__Service__Client
# ═══════════════════════════════════════════════════════════════════════════════

from mgraph_ai_service_cache_client.schemas.cache.data.Schema__Cache__Data__Store__Response import Schema__Cache__Data__Store__Response
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Data_Type              import Enum__Cache__Data_Type
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__Data_Key  import Safe_Str__Cache__File__Data_Key
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__File_Id   import Safe_Str__Cache__File__File_Id
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__Namespace       import Safe_Str__Cache__Namespace
from osbot_utils.type_safe.Type_Safe                                                        import Type_Safe
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                          import Cache_Id
from osbot_utils.type_safe.type_safe_core.decorators.type_safe                              import type_safe


class Cache__Entity__Data_File(Type_Safe):                                                                  # Bound client for data file operations
    cache_client : Cache__Service__Client                                                                   # Cache service client
    cache_id     : Cache_Id                                                                                 # Entity cache_id
    namespace    : Safe_Str__Cache__Namespace                                                               # Cache namespace
    data_key     : Safe_Str__Cache__File__Data_Key                                                          # Data layer path
    data_file_id : Safe_Str__Cache__File__File_Id                                                           # File identifier

    # ═══════════════════════════════════════════════════════════════════════════
    # Content Operations
    # ═══════════════════════════════════════════════════════════════════════════

    @type_safe
    def string(self) -> str:                                                                # Get content as string
        response = self.cache_client.data().retrieve().data__string__with__id_and_key(cache_id     = self.cache_id    ,
                                                                                      namespace    = self.namespace   ,
                                                                                      data_key     = self.data_key    ,
                                                                                      data_file_id = self.data_file_id)
        if type(response) is dict:                                                          # Handle error response
            return None
        if response:
            return response
        return None

    @type_safe
    def json(self) -> dict:                                                                 # Get content as JSON
        return self.cache_client.data().retrieve().data__json__with__id_and_key(cache_id     = self.cache_id    ,
                                                                                namespace    = self.namespace   ,
                                                                                data_key     = self.data_key    ,
                                                                                data_file_id = self.data_file_id)

    @type_safe
    def exists__data_type(self                                                    ,                    # Check if content exists
               data_type: Enum__Cache__Data_Type
          ) -> bool:
        result = self.cache_client.data().exists().data__exists__with__id_and_key(cache_id     = self.cache_id    ,
                                                                                  namespace    = self.namespace   ,
                                                                                  data_key     = self.data_key    ,
                                                                                  data_file_id = self.data_file_id,
                                                                                  data_type    = data_type        )
        if result:
            return result.exists
        return False

    def exists__json(self) -> bool:
       return self.exists__data_type(data_type=Enum__Cache__Data_Type.JSON)

    def exists__string(self) -> bool:
       return self.exists__data_type(data_type= Enum__Cache__Data_Type.STRING)

    @type_safe
    def store__string(self, content: str) -> Schema__Cache__Data__Store__Response:           # Store string content
        return self.cache_client.data_store().data__store_string__with__id_and_key(cache_id     = self.cache_id    ,
                                                                                   namespace    = self.namespace   ,
                                                                                   data_key     = self.data_key    ,
                                                                                   data_file_id = self.data_file_id,
                                                                                   body         = content          )

    @type_safe
    def store__json(self, data: dict) -> Schema__Cache__Data__Store__Response:               # Store JSON content
        return self.cache_client.data_store().data__store_json__with__id_and_key(cache_id     = self.cache_id    ,
                                                                                 namespace    = self.namespace   ,
                                                                                 data_key     = self.data_key    ,
                                                                                 data_file_id = self.data_file_id,
                                                                                 body         = data             )

    @type_safe
    def update__string(self, content: str) -> bool:                                          # Update string content
        result = self.cache_client.data().update().data__update_string__with__id_and_key(cache_id     = self.cache_id    ,
                                                                                         namespace    = self.namespace   ,
                                                                                         data_key     = self.data_key    ,
                                                                                         data_file_id = self.data_file_id,
                                                                                         body         = content          )
        if result:
            return result.success
        return False

    @type_safe
    def update__json(self, data: dict) -> bool:                                              # Update JSON content
        result = self.cache_client.data().update().data__update_json__with__id_and_key(cache_id     = self.cache_id    ,
                                                                                       namespace    = self.namespace   ,
                                                                                       data_key     = self.data_key    ,
                                                                                       data_file_id = self.data_file_id,
                                                                                       body         = data             )
        if result:
            return result.success
        return False

    @type_safe
    def delete__data_type(self                                                    ,                    # Delete content
                          data_type: Enum__Cache__Data_Type = Enum__Cache__Data_Type.STRING
                     ) -> bool:
        result = self.cache_client.data().delete().delete__data__file__with__id_and_key(cache_id     = self.cache_id    ,
                                                                                        namespace    = self.namespace   ,
                                                                                        data_key     = self.data_key    ,
                                                                                        data_file_id = self.data_file_id,
                                                                                        data_type    = data_type        )
        if result:
            return result.get('status') == 'success'
        return False