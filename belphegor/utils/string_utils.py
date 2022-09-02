import json
import re
import functools
from collections.abc import Callable
from urllib.parse import quote

#=============================================================================================================================#

class ProgressBar:
    def __init__(self, *, progress_message: str = "Working...", done_message: str = "Done.", length: int = 20):
        self.progress_message = progress_message
        self.done_message = done_message
        self.length = length

    def construct(self, rate: float):
        rate = max(min(rate, 1.0), 0.0)
        bf = "\u2588" * int(rate * self.length)
        c = "\u2591"
        return f"{bf:{c}<{self.length}} {rate * 100:.2f}%"

    def progress(self, rate: float):
        return f"{self.progress_message}\nProgress: {self.construct(rate)}"

    def done(self):
        return f"{self.done_message}\nProgress: {self.construct(1.0)}"

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

def safe_url(any_url):
    return quote(any_url, safe=r":/&$+,;=@#~%?")

_format_regex = re.compile(r"(?<!\\)\{([^\\]+?)\}")
def safe_format(text: str, **kwargs) -> str:
    return _format_regex.sub(lambda m: kwargs[m.group(1)], text)

_discord_regex = re.compile(r"[*_\[\]~`\\<>]")
def discord_escape(any_string):
    return _discord_regex.sub(lambda m: f"\\{m.group(0)}", any_string)

def split_iter(txt: str, *, check: Callable[[str], bool] = str.isspace, keep_delimiters: bool = True):
    word = []
    escape = False
    for c in txt:
        if escape:
            word.append(c)
            escape = False
        elif check(c):
            if word:
                yield "".join(word)
            word.clear()
            if keep_delimiters:
                yield c
        else:
            if c == "\\":
                escape = True
            word.append(c)
    else:
        if word:
            yield "".join(word)

def split_page(text: str, split_len: int, *, check: Callable[[str], bool] = str.isspace, safe_mode: bool = True, fix = "...", strip: str = None):
    if not text:
        return [""]
    description_page = []
    cur_node = []
    cur_len = 0
    len_fix = len(fix)
    if strip is None:
        clean = str.strip
    else:
        clean = lambda s: s.strip(strip)
    for word in split_iter(text, check=check):
        if safe_mode:
            if word.startswith(("http://", "https://")):
                word = safe_url(word)
            else:
                word = discord_escape(word)

        if cur_len + len(word) < split_len:
            cur_node.append(word)
            cur_len += len(word)
        else:
            if len(word) < split_len:
                description_page.append(f"{fix}{clean(''.join(cur_node))}{fix}")
            else:
                left = split_len - cur_len
                cur_node.append(word[:left])
                description_page.append(f"{fix}{clean(''.join(cur_node))}{fix}")
                stuff = (f"{fix}{clean(word[i+left:i+split_len+left])}{fix}" for i in range(0, len(word)-left, split_len))
                description_page.extend(stuff)
                word = description_page.pop(-1)[len_fix:-len_fix]
            cur_node = [word]
            cur_len = len(word)
    if cur_node:
        description_page.append(fix+clean(''.join(cur_node)))
    else:
        description_page[-1] = description_page[-1][:-len_fix]
    description_page[0] = description_page[0][len_fix:]
    return description_page