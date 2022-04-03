import json
import re
import functools
from collections.abc import Callable

#=============================================================================================================================#

_WHITESPACE = re.compile(r"\s*")

class ConcatJSONDecoder(json.JSONDecoder):
    def decode(self, s, _w=_WHITESPACE.match):
        s = s.strip()
        s_len = len(s)

        objs = []
        end = 0
        while end != s_len:
            obj, end = self.raw_decode(s, idx=_w(s, end).end())
            objs.append(obj)
        return objs

load_concat_json: Callable[[str], dict|list] = functools.partial(json.loads, cls=ConcatJSONDecoder)

#=============================================================================================================================#

def clean_codeblock(text: str) -> str:
    if text.startswith("```"):
        for i, c in enumerate(text):
            if c.isspace():
                break
        text = text[i:]
    text = text.strip("` \n\r\t\v\f")
    return text

_format_regex = re.compile(r"(?<!\\)\{([^\\]+?)\}")
def safe_format(text: str, **kwargs) -> str:
    return _format_regex.sub(lambda m: kwargs[m.group(1)], text)
