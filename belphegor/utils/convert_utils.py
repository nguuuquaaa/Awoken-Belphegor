

def to_int(n, *, base = 10, default: int = 0, strict = False) -> int:
    try:
        return int(n, base = base)
    except:
        if strict:
            raise
        else:
            return default