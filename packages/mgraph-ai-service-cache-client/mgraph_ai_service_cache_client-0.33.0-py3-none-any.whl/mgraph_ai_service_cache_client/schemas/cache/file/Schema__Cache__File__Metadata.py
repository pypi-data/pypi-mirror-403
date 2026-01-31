from memory_fs.schemas.Schema__Memory_FS__File__Metadata                               import Schema__Memory_FS__File__Metadata
from mgraph_ai_service_cache_client.schemas.cache.store.Schema__Cache__Store__Metadata import Schema__Cache__Store__Metadata

# todo: review the field name 'all_paths' (in light of the new file_paths field)
class Schema__Cache__File__Metadata(Schema__Memory_FS__File__Metadata):                 # ID-to-hash reference with content paths
    data: Schema__Cache__Store__Metadata                                                # overwrite data with this class