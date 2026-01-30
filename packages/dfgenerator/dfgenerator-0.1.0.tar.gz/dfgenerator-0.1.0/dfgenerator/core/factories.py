"""Value factories for generating column data."""

from __future__ import annotations

from typing import Any, Callable, Optional, Sequence

from .constants import DEFAULT_FAKER_LOCALE


def sequence(start: int = 1, step: int = 1) -> Callable[[int], int]:
    """Return a callable that yields a simple arithmetic sequence."""

    def factory(index: int) -> int:
        return start + (index * step)

    return factory


def choices(options: Sequence[Any]) -> Callable[[int], Any]:
    """Return a callable that cycles through the provided options."""
    if not options:
        raise ValueError("choices requires at least one option")

    def factory(index: int) -> Any:
        return options[index % len(options)]

    return factory


def _get_faker(locale: str, seed: Optional[int]):
    """
    Lazily create and cache a Faker instance for a locale/seed pair.
    """

    try:
        from faker import Faker  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError(
            "faker is required for faker_value(); install with `pip install faker`"
        ) from exc

    fake = Faker(locale)
    if seed is not None:
        fake.seed_instance(seed)
    return fake


def faker_value(
    provider: str,
    *,
    locale: Optional[str] = None,
    seed: Optional[int] = None,
    **kwargs: Any,
) -> Callable[[int], Any]:
    """
    Produce values using Faker providers.

    The returned callable ignores the row index; deterministic output can be
    achieved by passing a ``seed``.
    """

    faker_locale = locale or DEFAULT_FAKER_LOCALE

    validation_fake = _get_faker(faker_locale, seed)
    if not hasattr(validation_fake, provider):
        raise ValueError(f"Unknown Faker provider '{provider}' for locale {faker_locale}")

    def factory(index: int) -> Any:
        # Reseed per index when a seed is provided to make output deterministic across runs.
        fake = _get_faker(faker_locale, (seed + index) if seed is not None else None)
        fn = getattr(fake, provider)
        return fn(**kwargs) if kwargs else fn()

    return factory


def set_default_faker_locale(locale: str) -> None:
    """
    Set the default locale used by faker_value and config builders.
    """
    import dfgenerator.core.constants as constants

    constants.DEFAULT_FAKER_LOCALE = locale


__all__ = ["sequence", "choices", "faker_value", "set_default_faker_locale"]
