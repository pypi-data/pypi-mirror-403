from typing                                                                         import List
from osbot_utils.type_safe.Type_Safe                                                import Type_Safe
from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path   import Safe_Str__File__Path
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                  import Cache_Id
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id     import Safe_Str__Id


class Schema__Cache__Data__Files__List(Type_Safe):
    cache_id  : Cache_Id                 = None
    namespace : Safe_Str__Id                = None
    data_key  : Safe_Str__File__Path        = None
    data_files : List[Safe_Str__File__Path]