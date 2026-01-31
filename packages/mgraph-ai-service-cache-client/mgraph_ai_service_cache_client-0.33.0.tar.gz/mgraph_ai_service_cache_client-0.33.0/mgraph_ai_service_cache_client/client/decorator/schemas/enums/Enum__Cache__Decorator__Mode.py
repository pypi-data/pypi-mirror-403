from enum import Enum


class Enum__Cache__Decorator__Mode(str, Enum):                                  # Cache decorator operational modes
    ENABLED   = 'enabled'                                                       # Cache reads and writes enabled
    DISABLED  = 'disabled'                                                      # Cache completely bypassed
    READ_ONLY = 'read-only'                                                     # Only read from cache, never write
