from typing import Literal, TypeAlias

Threshold: TypeAlias = Literal[
    0,
    1,
    2,
    3,
    4,
    5,
    "unlimited",  # hint of suboptimal implementation
]
