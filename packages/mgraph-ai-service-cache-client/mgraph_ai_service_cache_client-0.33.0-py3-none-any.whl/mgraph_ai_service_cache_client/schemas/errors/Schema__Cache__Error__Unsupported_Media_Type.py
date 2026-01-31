from osbot_utils.type_safe.primitives.domains.common.safe_str.Safe_Str__Text                import Safe_Str__Text
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                          import Cache_Id
from osbot_utils.type_safe.primitives.domains.cryptography.safe_str.Safe_Str__Cache_Hash    import Safe_Str__Cache_Hash
from mgraph_ai_service_cache_client.schemas.errors.Schema__Cache__Error__Base               import Schema__Cache__Error__Base


class Schema__Cache__Error__Unsupported_Media_Type(Schema__Cache__Error__Base):       # 415 Unsupported Media Type errors
    requested_type : Safe_Str__Text                                                   # Type that was requested
    actual_type    : Safe_Str__Text                                                   # Actual type of the data
    cache_hash     : Safe_Str__Cache_Hash = None                                      # Hash of the entry (if applicable)
    cache_id       : Cache_Id          = None                                      # ID of the entry (if applicable)
