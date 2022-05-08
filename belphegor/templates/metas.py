from discord.utils import MISSING

#=============================================================================================================================#

class MetaItem(type):
    def __new__(meta, name, bases, namespace, **kwargs):
        cls = super().__new__(meta, name, bases, namespace, **kwargs)

        cls.__custom_view_item_init__ = getattr(cls, "__custom_view_item_init__", {}).copy()
        for key in getattr(cls, "__item_repr_attributes__", ()):
            value = cls.__dict__.get(key, MISSING)
            if value is not MISSING:
                delattr(cls, key)
                cls.__custom_view_item_init__[key] = value

        return cls

class BaseItem(metaclass = MetaItem):
    def __init__(self, **kwargs):
        new_kwargs = {**self.__custom_view_item_init__, **kwargs}
        super().__init__(**new_kwargs)
