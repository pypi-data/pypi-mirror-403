from typing import Union, Type, Dict
from osbot_utils.type_safe.Type_Safe                                              import Type_Safe
from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path import Safe_Str__File__Path
from osbot_utils.type_safe.primitives.domains.identifiers.safe_int.Timestamp_Now  import Timestamp_Now
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Data_Type    import Enum__Cache__Data_Type


class Schema__Cache__Decorator__Data(Type_Safe):
    cache_key      : Safe_Str__File__Path    = None
    data           : Union[Dict, str]        = None
    data_type      : Enum__Cache__Data_Type                 # todo: see if we need this, I think we might only need the type_safe_class
    type_safe_class: Type[Type_Safe]         = None         #  only set when data_type is Enum__Cache__Data_Type.TYPE_SAFE
    timestamp      : Timestamp_Now