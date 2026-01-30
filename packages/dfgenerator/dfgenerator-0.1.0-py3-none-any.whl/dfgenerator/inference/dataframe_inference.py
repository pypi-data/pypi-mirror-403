"""
Heuristics to infer generator configs from existing data (file or DataFrame).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from ..core.constants import DEFAULT_FAKER_LOCALE
from ..loaders.yaml_loader import build_from_config

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
UUID_RE = re.compile(
    r"^[a-f0-9]{8}-[a-f0-9]{4}-[1-5][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$",
    re.IGNORECASE,
)
PHONE_RE = re.compile(r"^[\d\-\+\s\(\)]{7,}$")


def _ensure_pandas():
    try:
        import pandas as pd  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError(
            "pandas is required for inference; install with `pip install pandas`"
        ) from exc
    return pd


def _infer_string(series) -> Dict[str, Any]:
    name = series.name or "col"
    lname = name.lower()
    # Email detection: name hint or regex on first non-null sample
    non_null = series.dropna()
    sample = str(non_null.iloc[0]) if not non_null.empty else ""
    if "email" in lname or EMAIL_RE.match(sample):
        return {"name": name, "faker": "email"}
    if "first" in lname and "name" in lname:
        return {"name": name, "faker": "first_name"}
    if ("last" in lname and "name" in lname) or "surname" in lname:
        return {"name": name, "faker": "last_name"}
    if lname in {"name", "fullname", "full_name"}:
        return {"name": name, "faker": "name"}
    if "phone" in lname or "mobile" in lname or PHONE_RE.match(sample or ""):
        return {"name": name, "faker": "phone_number"}
    if "city" in lname or "town" in lname:
        return {"name": name, "faker": "city"}
    if "country" in lname:
        return {"name": name, "faker": "country"}
    if "postcode" in lname or "zipcode" in lname or lname == "zip":
        return {"name": name, "faker": "postcode"}
    if "address" in lname or "street" in lname:
        return {"name": name, "faker": "street_address"}
    if "company" in lname:
        return {"name": name, "faker": "company"}
    if "job" in lname or "title" in lname:
        return {"name": name, "faker": "job"}
    if "iban" in lname:
        return {"name": name, "faker": "iban"}
    if "uuid" in lname or UUID_RE.match(sample or ""):
        return {"name": name, "faker": "uuid4"}

    # Low cardinality -> keep choices
    unique = list(dict.fromkeys(non_null.astype(str).tolist()))
    if 0 < len(unique) <= 10:
        return {"name": name, "choices": unique}

    return {"name": name, "faker": "word"}


def _infer_numeric(series) -> Dict[str, Any]:
    name = series.name or "col"
    lname = name.lower()
    non_null = series.dropna()
    if non_null.empty:
        return {"name": name, "sequence": {"start": 1, "step": 1}}
    if str(series.dtype).startswith(("int", "Int")):
        if "id" in lname:
            start = int(non_null.min())
            return {"name": name, "sequence": {"start": start, "step": 1}}
        start = int(non_null.min())
        return {"name": name, "sequence": {"start": start, "step": 1}}
    # float
    return {
        "name": name,
        "faker": "pyfloat",
        "kwargs": {"left_digits": 2, "right_digits": 2},
    }


def infer_config_from_df(
    df,
    *,
    faker_locale: Optional[str] = None,
    seed: Optional[int] = 123,
    base: Optional[Mapping[str, Any]] = None,
    rows: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Infer a generator configuration from a pandas DataFrame.
    """

    columns = []
    for col_name in df.columns:
        series = df[col_name]
        if str(series.dtype).startswith(("datetime", "datetime64")):
            columns.append({"name": col_name, "faker": "date_time"})
        elif str(series.dtype).startswith(("bool", "Boolean")):
            columns.append({"name": col_name, "choices": [True, False]})
        elif str(series.dtype).startswith(("int", "Int", "float")):
            columns.append(_infer_numeric(series))
        else:
            columns.append(_infer_string(series))

    return {
        "rows": rows if rows is not None else len(df),
        "faker_locale": faker_locale or DEFAULT_FAKER_LOCALE,
        "seed": seed,
        "base": dict(base or {}),
        "columns": columns,
    }


def infer_config_from_file(
    path: Path | str,
    *,
    faker_locale: Optional[str] = None,
    seed: Optional[int] = 123,
    base: Optional[Mapping[str, Any]] = None,
    rows: Optional[int] = None,
    **read_kwargs: Any,
) -> Dict[str, Any]:
    """
    Load a file with pandas and infer a generator configuration.
    Supports CSV (default) and JSON (via extension or `read_kwargs` override).
    """

    pd = _ensure_pandas()
    target = Path(path)
    suffix = target.suffix.lower()

    if read_kwargs:
        df = pd.read_csv(target, **read_kwargs)
    elif suffix == ".json":
        df = pd.read_json(target)
    else:
        df = pd.read_csv(target)

    return infer_config_from_df(
        df,
        faker_locale=faker_locale,
        seed=seed,
        base=base,
        rows=rows,
    )


def build_from_inferred(
    path: Path | str,
    *,
    faker_locale: Optional[str] = None,
    seed: Optional[int] = 123,
    base: Optional[Mapping[str, Any]] = None,
    rows: Optional[int] = None,
    **read_kwargs: Any,
):
    """
    Convenience wrapper: infer config from a file and build a DataSet.
    """

    config = infer_config_from_file(
        path,
        faker_locale=faker_locale,
        seed=seed,
        base=base,
        rows=rows,
        **read_kwargs,
    )
    return build_from_config(config)
