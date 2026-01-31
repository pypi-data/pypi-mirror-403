# ═══════════════════════════════════════════════════════════════════════════════
# Cache Service Client - Data Exists Operations
# Check if data files exist under cache entries
# ═══════════════════════════════════════════════════════════════════════════════

from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client__Requests          import Cache__Service__Client__Requests
from osbot_utils.type_safe.Type_Safe                                                              import Type_Safe
from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path                 import Safe_Str__File__Path
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                                import Cache_Id
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id                   import Safe_Str__Id
from osbot_utils.type_safe.type_safe_core.decorators.type_safe                                    import type_safe
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Data_Type                    import Enum__Cache__Data_Type
from mgraph_ai_service_cache_client.schemas.cache.data.Schema__Cache__Data__Exists__Response      import Schema__Cache__Data__Exists__Response


class Cache__Service__Client__Data__Exists(Type_Safe):                                         # Client for checking if data files exist
    requests : Cache__Service__Client__Requests

    @type_safe
    def data__exists__with__id(self,
                               cache_id     : Cache_Id              ,
                               namespace    : Safe_Str__Id          ,
                               data_type    : Enum__Cache__Data_Type,
                               data_file_id : Safe_Str__Id
                          ) -> Schema__Cache__Data__Exists__Response:                             # Check if data file exists by id

        path   = f"/{namespace}/cache/{cache_id}/data/exists/{data_type.value}/{data_file_id}"
        result = self.requests.execute(method = "GET",
                                       path   = path ,
                                       body   = None )

        if result.status_code == 200:
            return Schema__Cache__Data__Exists__Response.from_json(result.json())
        return None

    @type_safe
    def data__exists__with__id_and_key(self,
                                       cache_id     : Cache_Id              ,
                                       namespace    : Safe_Str__Id          ,
                                       data_type    : Enum__Cache__Data_Type,
                                       data_key     : Safe_Str__File__Path  ,
                                       data_file_id : Safe_Str__Id
                                  ) -> Schema__Cache__Data__Exists__Response:                     # Check if data file exists by id and key

        path   = f"/{namespace}/cache/{cache_id}/data/exists/{data_type.value}/{data_key}/{data_file_id}"
        result = self.requests.execute(method = "GET",
                                       path   = path ,
                                       body   = None )

        if result.status_code == 200:
            return Schema__Cache__Data__Exists__Response.from_json(result.json())
        return None