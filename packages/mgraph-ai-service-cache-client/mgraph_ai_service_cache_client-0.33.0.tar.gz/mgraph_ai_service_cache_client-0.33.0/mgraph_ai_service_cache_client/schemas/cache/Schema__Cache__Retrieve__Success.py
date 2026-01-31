from typing                                                                              import Union
from osbot_utils.type_safe.Type_Safe                                                     import Type_Safe
from mgraph_ai_service_cache_client.schemas.cache.Schema__Cache__Metadata                import Schema__Cache__Metadata
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Data_Type           import Enum__Cache__Data_Type

# todo: refactor with Schema__Cache__Binary__Reference since it is a mess that the retrieve method returns two different types
# Success response for retrieving data
class Schema__Cache__Retrieve__Success(Type_Safe):        # Successful retrieval with data
    data      : Union[dict, str, bytes]                   # Actual cached content
    metadata  : Schema__Cache__Metadata                   # Cache metadata
    data_type : Enum__Cache__Data_Type                    # Type of data returned
