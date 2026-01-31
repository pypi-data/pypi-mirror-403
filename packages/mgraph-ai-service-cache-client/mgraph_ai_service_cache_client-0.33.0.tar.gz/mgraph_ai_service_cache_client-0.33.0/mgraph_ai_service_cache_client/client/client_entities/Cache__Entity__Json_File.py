# ═══════════════════════════════════════════════════════════════════════════════
# Cache__Entity__Json_File
# ═══════════════════════════════════════════════════════════════════════════════

from mgraph_ai_service_cache_client.client.client_entities.Cache__Entity__Data_File         import Cache__Entity__Data_File
from mgraph_ai_service_cache_client.schemas.cache.data.Schema__Cache__Data__Store__Response import Schema__Cache__Data__Store__Response
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Data_Type              import Enum__Cache__Data_Type


class Cache__Entity__Json_File(Cache__Entity__Data_File):                   # JSON-focused data file

    def exists(self) -> bool:                                               # Check if JSON file exists
        return self.exists__json()

    def retrieve(self) -> dict:                                             # Get JSON content
        return self.json()

    def store(self, data: dict) -> Schema__Cache__Data__Store__Response:    # Store JSON content
        return self.store__json(data)

    def update(self, data: dict) -> bool:                                   # Update JSON content
        return self.update__json(data)

    def delete(self) -> bool:                                               # Delete JSON file
        return super().delete__data_type(data_type=Enum__Cache__Data_Type.JSON)