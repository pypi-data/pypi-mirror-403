from osbot_utils.type_safe.Type_Safe                                                     import Type_Safe
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                       import Cache_Id
from osbot_utils.type_safe.primitives.domains.identifiers.safe_int.Timestamp_Now         import Timestamp_Now


class Schema__Cache__Hash__Entry(Type_Safe):       # Individual cache ID entry in hash reference
    cache_id   : Cache_Id                       # Cache ID
    timestamp : Timestamp_Now