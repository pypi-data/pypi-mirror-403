"""

run with :

uv run -p 3.9 python -m tgzr.pipeline.asset.asset_plugins.asset_with_params.xx

and:

uv run -p 3.12 python -m tgzr.pipeline.asset.asset_plugins.asset_with_params.xx


"""

from __future__ import annotations
from typing import Optional, Union, get_type_hints

import sys

print("Testing stuff...")

from .params_panel import is_union_type

ok = "✅"
bad = "‼️"


if 0:

    class C:
        optional: Optional[str]
        union: Union[str, None]
        pipe: str | None

    def test(c):
        for name, ann in get_type_hints(c).items():
            rez = ok
            if not is_union_type(ann):
                rez = bad
            print("--->", ann, type(ann), rez)

    test(C)


T = Union[str, None]
print(T, type(T), is_union_type(T) and ok or bad)
T = Optional[str]
print(T, type(T), is_union_type(T) and ok or bad)

if sys.version_info > (3, 10):
    T = str | None
    print(T, type(T), is_union_type(T) and ok or bad)
