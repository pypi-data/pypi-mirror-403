# import json
# from typing                                                                                     import Any, Dict
# from osbot_utils.type_safe.Type_Safe                                                            import Type_Safe
# from osbot_utils.type_safe.Type_Safe__Primitive                                                 import Type_Safe__Primitive
# from osbot_utils.type_safe.primitives.domains.cryptography.safe_str.Safe_Str__Hash              import Safe_Str__Hash
# from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path               import Safe_Str__File__Path
# from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Python__Identifier import Safe_Str__Python__Identifier
# from osbot_utils.type_safe.type_safe_core.collections.Type_Safe__List                           import Type_Safe__List
# from osbot_utils.type_safe.type_safe_core.decorators.type_safe                                  import type_safe
# from osbot_utils.utils.Misc                                                                     import str_md5
# from mgraph_ai_service_cache_client.client.decorator.schemas.Schema__Cache__Decorator__Config   import Schema__Cache__Decorator__Config
#
#
# class Cache__Decorator__Key__Generator(Type_Safe):                                         # Generates cache keys from method parameters and configuration
#
#     @type_safe
#     def generate(self,                                                          # Generate cache_key path for storage
#                  config      : Schema__Cache__Decorator__Config,                # Cache configuration
#                  class_name  : Safe_Str__Python__Identifier,                                             # Name of the class containing the method
#                  method_name : Safe_Str__Python__Identifier,                                             # Name of the cached method
#                  **params                                                       # Method parameters (keyword arguments)
#             ) -> Safe_Str__File__Path:                                                           # Cache key path (e.g., "Class/method/abc123")
#
#         parts = Type_Safe__List(expected_type=Type_Safe__Primitive)                                                              # Build cache_key path components
#
#         if config.use_class_name:                                               # Add class name to path
#             parts.append(class_name)
#
#         if config.use_method_name:                                              # Add method name to path
#             parts.append(method_name)
#
#         if config.key_fields:                                                   # Generate hash from key_fields
#             key_data = self._extract_key_data(params, config.key_fields)
#             hash_value = self._hash_data(key_data)
#             parts.append(hash_value)
#
#         return "/".join(parts)                                                  # Return path like "Text__Transformation__Service/transform/abc123def456"
#
#     # todo: review this in light with the Type_Safe features I have and capabilties like Safe_Str__Json__Field_Path
#     #       I think we can simplify and improve the performance of this workflow
#     @type_safe
#     def _extract_key_data(self,                                                 # Extract relevant params for cache key
#                           params     : Dict[str, Any],                          # All method parameters
#                           key_fields : list                                     # Field names to extract
#                      ) -> Dict[str, Any]:                                       # Extracted key data
#
#         key_data = {}
#
#         for field in key_fields:
#             field_str = str(field)
#             if field_str in params:
#                 value = params[field_str]
#                 key_data[field_str] = self._serialize_value(value)                  # Serialize value for hashing
#
#         return key_data
#
#     # todo: review how this method is working since we already have really good serialization support in Type_Safe and Type_Safe__Primitive
#     #@type_safe # this is not doing anything in Any->ANY
#     def _serialize_value(self, value: Any) -> Any:                              # Serialize value for consistent hashing
#         from osbot_utils.type_safe.Type_Safe import Type_Safe                   # Import here to avoid circular dependency
#
#         if isinstance(value, Type_Safe):                                        # Type_Safe objects → dict (via json())
#             return value.json()
#         elif isinstance(value, dict):                                           # Dicts → recursively serialize values
#             return {k: self._serialize_value(v) for k, v in value.items()}
#         elif isinstance(value, (list, tuple)):                                  # Lists/tuples → recursively serialize items
#             return [self._serialize_value(item) for item in value]
#         elif hasattr(value, '__dict__'):                                        # Objects with __dict__ → dict
#             return {k: self._serialize_value(v) for k, v in value.__dict__.items()}
#         else:                                                                   # Primitives → as-is (str, int, float, bool, None)
#             return value
#
#     @type_safe
#     def _hash_data(self, data: dict) -> Safe_Str__Hash:                                    # Generate consistent hash from data
#         json_str = json.dumps(data, sort_keys=True, default=str)               # Serialize to JSON with sorted keys
#         hash_value = str_md5(json_str)[:10]                                     # MD5 hash, take first 10 chars
#         return hash_value
