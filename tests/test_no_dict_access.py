"""No dictionaries outside the parsing boundary.

JSON is parsed eagerly into the typed dataclasses of obs_studio_libs/model.py,
which is the only module allowed to touch JSON objects. Anywhere else these
are errors:
  x["key"]                a string-keyed subscript
  x.get("key"), x.setdefault("key", ...), x.pop("key")
  {"key": ...}            a dict literal with string keys
  dict(...)               building a dictionary
Use the model's attributes (asset.urls) instead.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = ROOT / "obs_studio_libs" / "model.py"
CHECKED = sorted(p for d in ("obs_studio_libs", "tests") for p in (ROOT / d).rglob("*.py") if p != BOUNDARY)


def violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), str(path))
    out = []
    for node in ast.walk(tree):
        where = f"{path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name}:{getattr(node, 'lineno', 0)}"
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, str)
        ):
            out.append(f"{where}: subscript [{node.slice.value!r}]")
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in ("get", "setdefault", "pop")
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            out.append(f"{where}: .{node.func.attr}({node.args[0].value!r})")
        elif isinstance(node, ast.Dict) and any(
            isinstance(k, ast.Constant) and isinstance(k.value, str) for k in node.keys
        ):
            out.append(f"{where}: dict literal")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
            out.append(f"{where}: dict()")
    return out


def test_no_dict_access_outside_the_model():
    found = [v for p in CHECKED for v in violations(p)]
    assert not found, "dictionaries outside obs_studio_libs/model.py:\n" + "\n".join(found)


def test_the_check_catches_each_form(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text('a = x["urls"]\nb = x.get("urls")\nc = {"k": 1}\nd = dict(k=1)\ne = x.setdefault("k", 1)\n')
    kinds = [v.split(": ", 1)[1] for v in violations(bad)]
    assert kinds == ["subscript ['urls']", ".get('urls')", "dict literal", "dict()", ".setdefault('k')"]
