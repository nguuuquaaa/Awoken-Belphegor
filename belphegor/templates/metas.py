from discord.utils import MISSING
from pydantic.fields import Field, FieldInfo
import inspect

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

        return super().__new__(meta, name, bases, namespace, **kwargs)

class MetaMergeClasstypeProperty(type):
    @staticmethod
    def merge_classes(name: str, classes: tuple[type]):
        if len(classes) == 1:
            return classes[0]

        namespace = {}
        for i, cls in enumerate(classes[:-1]):
            for key in dir(cls):
                if not key.startswith("__"):
                    value = getattr(cls, key)
                    if isinstance(value, type):
                        subs = {value: 1}
                        for nex in classes[i+1:]:
                            v = getattr(nex, key, None)
                            if isinstance(v, type):
                                subs[v] = 1

                        namespace[key] = MetaMergeClasstypeProperty.merge_classes(key, tuple(subs.keys()))

                elif key == "__custom_ui_init_items__":
                    __custom_ui_init_items__ = cls.__custom_ui_init_items__
                    for nex in classes[i+1:]:
                        v = getattr(nex, key, {})
                        __custom_ui_init_items__ = {**v, **__custom_ui_init_items__}

                    namespace[key] = __custom_ui_init_items__

        cls = type(name, tuple(classes), namespace)
        log.debug(getattr(cls, "title", "xxx"))
        return cls

    def __new__(meta, name, bases, namespace, **kwargs):
        to_be_merged = {}
        for key, value in namespace.items():
            if isinstance(value, type):
                subs = {value: 1}
                for base in bases:
                    v = getattr(base, key, None)
                    if isinstance(v, type):
                        subs[v] = 1

                to_be_merged[key] = MetaMergeClasstypeProperty.merge_classes(key, tuple(subs.keys()))

        namespace.update(to_be_merged)
        return super().__new__(meta, name, bases, namespace, **kwargs)

class MetaMergeClasstypePropertyItem(MetaItem, MetaMergeClasstypeProperty):
    pass

class PostInitable:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        post_init = getattr(self, "__post_init__", None)
        if post_init:
            post_init()

class BaseItem(PostInitable, metaclass = MetaMergeClasstypePropertyItem):
    def __init__(self, **kwargs):
        new_kwargs = {**self.__custom_ui_init_items__, **kwargs}
        super().__init__(**new_kwargs)
