from collections.abc import Callable
from typing import Literal

type OnProgress = Callable[[float], None]
type OperationStatus = Literal["created", "processing", "completed", "failed", "stopped"]
