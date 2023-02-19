from collections.abc import Iterable
import re

class QueryTemplate:
    @staticmethod
    def match_any(name: str, fields: Iterable[str]) -> list[dict]:
        return [
            {
                field: {
                    "$regex": ".*?".join(map(re.escape, name.split())),
                    "$options": "i"
                }
            } for field in fields
        ]