from collections.abc import Iterable
import re

def match_any(name: str, fields: Iterable[str]) -> dict[str, list[dict]]:
    return {
        "$or": [
            {
                field: {
                    "$regex": ".*?".join(map(re.escape, name.split())),
                    "$options": "i"
                }
            } for field in fields
        ]
    }
