from discord.utils import MISSING
from pydantic.fields import Field, FieldInfo
import typing

from belphegor import utils

#=============================================================================================================================#

log = utils.get_logger()

#=============================================================================================================================#

@utils.__dataclass_transform__(kw_only_default = True, field_specifiers = (Field, FieldInfo))
class MetaItem(type):
    def __new__(meta, name, bases, namespace, **kwargs):
        init_fields = None
        __custom_ui_init_items__ = {}
        for base in reversed(bases):
            init_fields = getattr(base, "__custom_ui_init_fields__", init_fields)
            __custom_ui_init_items__.update(getattr(base, "__custom_ui_init_items__", {}))
        init_fields = namespace.get("__custom_ui_init_fields__", init_fields)

        if init_fields:
            for key in init_fields:
                value = namespace.pop(key, None)
                if value:
                    __custom_ui_init_items__[key] = value

        namespace["__custom_ui_init_items__"] = __custom_ui_init_items__

        cls = super().__new__(meta, name, bases, namespace, **kwargs)
        return cls

class BaseItem(metaclass = MetaItem):
    def __init__(self, **kwargs):
        new_kwargs = {**self.__custom_ui_init_items__, **kwargs}
        super().__init__(**new_kwargs)
        post_init = getattr(self, "__post_init__", None)
        if post_init:
            post_init()
