"""
Helpers for gdsofa: Munch, path/iterable utilities, JSON encoding.

- **From gdutils** (see https://gdutils-a2ef81.gitlabpages.inria.fr/): `load_json`, `dump_json`,
  `Timer`, and `get_iterable` (re-exported as `as_iterable`). This avoids duplicating logic
  already provided by the gdutils library.
- **gdsofa-specific**: `dump_json` wraps gdutils to create parent directories; `dump_path`,
  `Munch` / `munchify`, `JsonEncoder`, `StdRedirect`, and path/string helpers remain here.
"""
import contextlib
import json
import logging
import string
import random
import sys
import uuid
from pathlib import Path
from typing import Any, Union

import gdutils
import randomname

# Reuse from gdutils to avoid redundancy (https://gdutils-a2ef81.gitlabpages.inria.fr/)
load_json = gdutils.load_json
Timer = gdutils.Timer
get_iterable = gdutils.get_iterable
as_iterable = get_iterable  # backward-compatible alias

__all__ = [
    "random_name",
    "Munch",
    "munchify",
    "as_iterable",
    "get_iterable",
    "none_default",
    "unique_id",
    "make_string",
    "ensure_ext",
    "path_insert_before",
    "JsonEncoder",
    "load_json",
    "dump_json",
    "dump_path",
    "Timer",
    "StdRedirect",
]

log = logging.getLogger(__name__)


def random_name():
    try:
        return randomname.get_name(sep="_")
    except Exception:
        chars = string.ascii_letters + string.digits
        return "".join(random.choices(chars, k=6))


class Munch(dict):
    """Dict with attribute access (replaces tf.munchify / treefiles Munch)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for k, v in self.items():
            if isinstance(v, dict) and not isinstance(v, Munch):
                self[k] = Munch(v)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(key) from e

    def __setattr__(self, key, value):
        self[key] = value


def munchify(obj: Any) -> Munch:
    """Convert dict (and nested dicts) to Munch."""
    if isinstance(obj, dict):
        return Munch({k: munchify(v) for k, v in obj.items()})
    if isinstance(obj, (list, tuple)):
        return type(obj)(munchify(x) for x in obj)
    return obj


def none_default(a: Any, b: Any) -> Any:
    """Return a if a is not None else b (replaces tf.none)."""
    return a if a is not None else b


def unique_id() -> str:
    """Return a unique string (e.g. for treelib node IDs). Replaces tf.get_string()."""
    return uuid.uuid4().hex


def make_string(**kwargs: Any) -> str:
    """Format key=value for logging (replaces tf.make_string)."""
    return ", ".join(f"{k}={v!r}" for k, v in kwargs.items())


def ensure_ext(fname: Union[str, Path], ext: str) -> Path:
    """Ensure path has the given extension (e.g. '.json'). Replaces tf.ensure_ext."""
    p = Path(fname)
    if not ext.startswith("."):
        ext = "." + ext
    if p.suffix != ext:
        p = p.with_suffix(ext)
    return p


def path_insert_before(fname: Union[str, Path], suffix: str, insert: str) -> Path:
    """E.g. path_insert_before('a/b/foo.json', '.json', '_schema') -> a/b/foo_schema.json."""
    p = Path(fname)
    return p.with_stem(p.stem + insert)


def dump_path(path: Union[str, Path]) -> Path:
    """Create directory (parents, exist_ok) and return resolved path. Replaces tf.dump."""
    p = Path(path).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


class JsonEncoder(json.JSONEncoder):
    """JSON encoder for Path, numpy types (replaces tf.JsonEncoder)."""

    def default(self, o):
        if isinstance(o, Path):
            return str(o)
        try:
            import numpy as np
            if isinstance(o, (np.integer, np.floating)):
                return float(o) if isinstance(o, np.floating) else int(o)
            if isinstance(o, np.ndarray):
                return o.tolist()
        except ImportError:
            pass
        return super().default(o)


def dump_json(path: Union[str, Path], data: Any, **kwargs) -> None:
    """Write JSON file; creates parent dirs. Wraps gdutils.dump_json."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    gdutils.dump_json(path, data, **kwargs)


@contextlib.contextmanager
def StdRedirect(stream, fname: Union[str, Path]):
    """Redirect stream to a file (replaces tf.StdRedirect)."""
    path = Path(fname)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        if stream is sys.stdout:
            with contextlib.redirect_stdout(f):
                yield f
        elif stream is sys.stderr:
            with contextlib.redirect_stderr(f):
                yield f
        else:
            raise ValueError("stream must be sys.stdout or sys.stderr")
