from enum import Enum

class Enum__Cache__Data_Type(str, Enum):
    JSON      = "json"
    STRING    = "string"
    BINARY    = "binary"
    TYPE_SAFE = "type-safe"                             # todo: review this use, since at the moment this is not really being used