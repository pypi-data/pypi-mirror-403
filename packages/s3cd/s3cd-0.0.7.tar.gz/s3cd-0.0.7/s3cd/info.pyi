from _typeshed import Incomplete
from s3cd.settings import AppSettings as AppSettings
from typing import Any

class ReleaseInfoGenerator:
    config: Incomplete
    def __init__(self) -> None: ...
    def generate(self) -> dict[str, Any]: ...
