import hashlib
import json
import logging
from typing import Any, Dict, List, Union
from osbot_utils.type_safe.Type_Safe                                                            import Type_Safe
from osbot_utils.type_safe.Type_Safe__Primitive                                                 import Type_Safe__Primitive
from osbot_utils.type_safe.primitives.domains.cryptography.safe_str.Safe_Str__Cache_Hash        import Safe_Str__Cache_Hash
from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path               import Safe_Str__File__Path
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Json__Field_Path   import Safe_Str__Json__Field_Path
from osbot_utils.type_safe.primitives.domains.python.safe_str.Safe_Str__Python__Identifier      import Safe_Str__Python__Identifier
from osbot_utils.type_safe.type_safe_core.decorators.type_safe                                  import type_safe
from osbot_utils.helpers.cache.Cache__Hash__Generator                                           import Cache__Hash__Generator
from mgraph_ai_service_cache_client.client.decorator.schemas.Schema__Cache__Decorator__Config   import Schema__Cache__Decorator__Config

logger = logging.getLogger(__name__)


class Cache__Key__Builder(Type_Safe):           # Builds cache keys leveraging Type_Safe primitives for robust key generation.
    hash_generator: Cache__Hash__Generator

    @type_safe
    def build_cache_key(self,                                               # Build a cache key path for storage.
                        config      : Schema__Cache__Decorator__Config,     # Cache configuration
                        class_name  : Safe_Str__Python__Identifier,         # Name of the class containing the method
                        method_name : Safe_Str__Python__Identifier,         # Name of the cached method
                        params      : Dict[str, Any]                        # Method parameters
                   ) -> Safe_Str__File__Path:                               # Cache key path suitable for file storage

        path_components = []

        if config.use_class_name and class_name:                            # Add class name if configured
            path_components.append(str(class_name))

        if config.use_method_name and method_name:                          # Add method name if configured
            path_components.append(str(method_name))

        if config.key_fields:                                               # Generate hash from specified fields or all params
            key_data = self._extract_key_fields(params, config.key_fields)  # Extract only specified fields
        else:
            key_data = params                                               # Use all parameters

        if key_data:                                                        # Generate hash if we have data
            param_hash = self._generate_param_hash(key_data)
            path_components.append(param_hash)

        if path_components:                                                 # Join components with '/'
            cache_key = "/".join(path_components)
            return Safe_Str__File__Path(cache_key)
        else:
            return Safe_Str__File__Path("default/cache")                    # Fallback to a default key if no components

    @type_safe
    def build_cache_hash(self,                                              # Generate a cache hash from a cache key.
                         data : Union[dict, str, bytes]
                         #cache_key: Safe_Str__File__Path                    # The cache key path
                    ) -> Safe_Str__Cache_Hash:                              # A cache hash suitable for hash-based lookups
        hash_value = None
        if  isinstance(data, str):
            hash_value = self.hash_generator.from_string(data)
        elif  isinstance(data, bytes):
            hash_value = self.hash_generator.from_bytes(data)
        elif isinstance(data, dict):
            hash_value = self.hash_generator.from_json(data)
        return hash_value

    @type_safe
    def _extract_key_fields(self,
                           params: Dict[str, Any],
                           key_fields: List[str]
                          ) -> Dict[str, Any]:
        """
        Extract specified fields from parameters using Type_Safe field path support.
        
        Args:
            params: All method parameters
            key_fields: List of field names/paths to extract
            
        Returns:
            Dictionary with only the specified fields
        """
        extracted = {}
        
        for field in key_fields:
            field_str = str(field)
            
            # Handle nested field paths (e.g., "user.id", "config.cache.enabled")
            if '.' in field_str:
                # Use Safe_Str__Json__Field_Path for nested access
                field_path = Safe_Str__Json__Field_Path(field_str)
                value = self.get_nested_value(params, field_path)
                if value is not None:
                    extracted[field_str] = value
            else:
                # Direct field access
                if field_str in params:
                    extracted[field_str] = params[field_str]
        
        return extracted

    @type_safe
    def get_nested_value(self,                                                  # Get nested value from object using field path.
                         obj       : Any,                                       # Object to extract from (dict or Type_Safe)
                         field_path: Safe_Str__Json__Field_Path                 # Dot-separated field path
                    ) -> Any:                                                   # Value at the field path or None
        path_parts = str(field_path).split('.')
        current = obj
        
        for part in path_parts:
            if current is None:
                return None

            if isinstance(current, dict):                                       # Handle dict access
                current = current.get(part)
            elif isinstance(current, Type_Safe):                                # Handle Type_Safe object access
                current = getattr(current, part, None)
            elif hasattr(current, part):                                        # Handle regular object attribute access
                current = getattr(current, part)
            else:
                return None
        
        return current

    @type_safe
    def _generate_param_hash(self, 
                            key_data: Dict[str, Any]
                           ) -> str:
        """
        Generate a hash from parameter data using Type_Safe serialization.
        
        Args:
            key_data: Dictionary of parameters to hash
            
        Returns:
            Hash string (first 10 characters of MD5)
        """
        # Convert Type_Safe objects to JSON for consistent hashing
        normalized_data = self._normalize_for_hashing(key_data)
        
        # Create deterministic JSON string
        json_str = json.dumps(normalized_data, sort_keys=True, default=str)
        
        # Generate hash (use first 10 chars for brevity)
        hash_value = hashlib.md5(json_str.encode()).hexdigest()[:10]
        
        return hash_value

    @type_safe
    def _normalize_for_hashing(self, obj: Any) -> Any:
        """
        Normalize objects for consistent hashing.
        
        Converts Type_Safe objects to dictionaries and handles
        other special types to ensure deterministic hashing.
        
        Args:
            obj: Object to normalize
            
        Returns:
            Normalized representation
        """
        # Type_Safe objects → dict
        if isinstance(obj, Type_Safe):
            return obj.json()
        
        # Type_Safe__Primitive → value
        elif isinstance(obj, Type_Safe__Primitive):
            return obj.value()
        
        # Dict → recursively normalize values
        elif isinstance(obj, dict):
            return {k: self._normalize_for_hashing(v) for k, v in obj.items()}
        
        # List/tuple → recursively normalize items
        elif isinstance(obj, (list, tuple)):
            return [self._normalize_for_hashing(item) for item in obj]
        
        # Bytes → hex string for JSON compatibility
        elif isinstance(obj, bytes):
            return obj.hex()
        
        # Primitives → as-is
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        
        # Objects with __dict__ → normalize dict
        elif hasattr(obj, '__dict__') and not callable(obj):
            return self._normalize_for_hashing(obj.__dict__)
        
        # Default → string representation
        else:
            return str(obj)

    @type_safe
    def build_namespace_key(self,
                           namespace: str,
                           cache_key: Safe_Str__File__Path
                          ) -> Safe_Str__File__Path:
        """
        Build a full namespaced cache key.
        
        Args:
            namespace: Cache namespace
            cache_key: Base cache key
            
        Returns:
            Full path including namespace
        """
        full_path = f"{namespace}/{cache_key}"
        return Safe_Str__File__Path(full_path)
