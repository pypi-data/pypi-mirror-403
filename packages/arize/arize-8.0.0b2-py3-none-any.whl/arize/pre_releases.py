"""Pre-release feature management and gating for the Arize SDK."""

import functools
import logging
from collections.abc import Callable
from enum import StrEnum
from typing import TypeVar

from arize.version import __version__

logger = logging.getLogger(__name__)


class ReleaseStage(StrEnum):
    """Enum representing the release stage of API features."""

    ALPHA = "alpha"
    BETA = "beta"


_WARNED: set[str] = set()

_F = TypeVar("_F", bound=Callable)


def _format_prerelease_message(*, key: str, stage: ReleaseStage) -> str:
    article = "an" if stage is ReleaseStage.ALPHA else "a"
    return (
        f"[{stage.upper()}] {key} is {article} {stage} API "
        f"in Arize SDK v{__version__} and may change without notice."
    )


def prerelease_endpoint(*, stage: ReleaseStage, key: str) -> Callable[[_F], _F]:
    """Decorate a method to emit a prerelease warning via logging once per process."""

    def deco(fn: _F) -> _F:
        @functools.wraps(fn)
        def wrapper(*args: object, **kwargs: object) -> object:
            if key not in _WARNED:
                _WARNED.add(key)
                logger.warning(_format_prerelease_message(key=key, stage=stage))
            return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return deco
