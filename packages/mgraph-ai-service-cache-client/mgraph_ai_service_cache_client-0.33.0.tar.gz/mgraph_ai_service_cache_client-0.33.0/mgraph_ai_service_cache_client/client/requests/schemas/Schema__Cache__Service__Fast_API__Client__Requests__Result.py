from typing                             import Union, Dict, List, Optional
from osbot_utils.type_safe.Type_Safe    import Type_Safe

# todo: refactor this name to a smaller name :)
class Schema__Cache__Service__Fast_API__Client__Requests__Result(Type_Safe):
    status_code : int
    #json        : Optional[Dict] = None                                            # BUG, mising list
    json        : Union[Dict,List] = None
    text        : Optional[str]    = None
    content     : bytes            = b""
    #headers     : Dict[str, str] = {}                                              # BUG: we can't do this with Type_Safe (this will be allocated on __init__)
    headers     : Dict[str, str]
    path        : str            = ""