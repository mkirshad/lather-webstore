from __future__ import annotations

from functools import wraps
from typing import Any, Callable


class Celery:
    """Lightweight stand-in for Celery that executes tasks synchronously."""

    def __init__(self, name: str):
        self.name = name

    def config_from_object(self, obj: str, namespace: str = "CELERY") -> None:  # pragma: no cover
        return None

    def autodiscover_tasks(self) -> None:  # pragma: no cover
        return None


def shared_task(*dargs: Any, **dkwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def delay(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        func.delay = delay  # type: ignore[attr-defined]
        func.apply_async = delay  # type: ignore[attr-defined]
        return func

    if dargs and callable(dargs[0]):
        return decorator(dargs[0])
    return decorator


__all__ = ["Celery", "shared_task"]
