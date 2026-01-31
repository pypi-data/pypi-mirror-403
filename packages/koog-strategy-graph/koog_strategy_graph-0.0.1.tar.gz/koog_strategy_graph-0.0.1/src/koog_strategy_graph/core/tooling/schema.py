from __future__ import annotations

import inspect
from dataclasses import MISSING, fields, is_dataclass
from typing import Any, Dict, List, Optional, Union, get_args, get_origin, get_type_hints


def _is_optional(tp: Any) -> bool:
    origin = get_origin(tp)
    if origin is Union:
        args = get_args(tp)
        return any(a is type(None) for a in args)  # noqa: E721
    return False


def _strip_optional(tp: Any) -> Any:
    origin = get_origin(tp)
    if origin is Union:
        args = [a for a in get_args(tp) if a is not type(None)]  # noqa: E721
        if len(args) == 1:
            return args[0]
    return tp


def _schema_for_type(tp: Any) -> Dict[str, Any]:
    """
    Best-effort JSON Schema for a python type hint.

    Keep this intentionally small/simple to avoid overengineering:
    - primitives: str/int/float/bool
    - Optional[T]
    - list[T]
    - dict[str, Any] (object)
    - dataclasses (object with fields)
    - fallback: permissive object
    """
    if tp is Any or tp is object or tp is None:
        return {"type": "object", "additionalProperties": True}

    # Optional[T]
    if _is_optional(tp):
        inner = _strip_optional(tp)
        sch = _schema_for_type(inner)
        # JSON Schema draft differences aside, keep it simple:
        return {"anyOf": [sch, {"type": "null"}]}

    origin = get_origin(tp)
    args = get_args(tp)

    # list[T]
    if origin in (list, List):
        item_tp = args[0] if args else Any
        return {"type": "array", "items": _schema_for_type(item_tp)}

    # dict[K, V] -> object
    if origin in (dict, Dict):
        # If key type isn't str, still treat as object.
        value_tp = args[1] if len(args) >= 2 else Any
        return {"type": "object", "additionalProperties": _schema_for_type(value_tp)}

    # Union[T1, T2, ...]
    if origin is Union:
        return {"anyOf": [_schema_for_type(a) for a in args]}

    # Dataclass
    if isinstance(tp, type) and is_dataclass(tp):
        props: Dict[str, Any] = {}
        required: List[str] = []
        type_hints = get_type_hints(tp)
        for f in fields(tp):
            f_tp = type_hints.get(f.name, Any)
            props[f.name] = _schema_for_type(f_tp)
            if not _is_optional(f_tp) and f.default is MISSING and f.default_factory is MISSING:
                required.append(f.name)
        out: Dict[str, Any] = {"type": "object", "properties": props, "additionalProperties": False}
        if required:
            out["required"] = required
        return out

    # Primitives
    if tp is str:
        return {"type": "string"}
    if tp is int:
        return {"type": "integer"}
    if tp is float:
        return {"type": "number"}
    if tp is bool:
        return {"type": "boolean"}

    # Literal/Enum/etc: keep permissive for now
    return {"type": "object", "additionalProperties": True}


def schema_from_signature(
    fn: Any,
    *,
    include_descriptions: bool = False,
) -> Dict[str, Any]:
    """
    Build a JSON schema for a function that takes exactly one argument (a structured args object).

    Convention:
    - if the function has a single parameter (besides `self`), we describe that parameter's fields:
      - dict-like -> object
      - dataclass -> object properties
      - otherwise -> object with one property named after the parameter
    """
    sig = inspect.signature(fn)
    params = [p for p in sig.parameters.values() if p.name != "self"]
    hints = get_type_hints(fn)

    if len(params) == 0:
        return {"type": "object", "properties": {}, "additionalProperties": False}

    if len(params) == 1:
        p = params[0]
        tp = hints.get(p.name, Any)
        sch = _schema_for_type(tp)
        # Ensure we always return an object schema for tool args.
        if sch.get("type") == "object" or "properties" in sch:
            return sch
        return {"type": "object", "properties": {p.name: sch}, "required": [p.name], "additionalProperties": False}

    # Multi-arg functions: represent as object{argName: schema}
    props: Dict[str, Any] = {}
    required: List[str] = []
    for p in params:
        tp = hints.get(p.name, Any)
        props[p.name] = _schema_for_type(tp)
        if p.default is inspect._empty and not _is_optional(tp):
            required.append(p.name)
    out: Dict[str, Any] = {"type": "object", "properties": props, "additionalProperties": False}
    if required:
        out["required"] = required
    if include_descriptions:
        # Keep hook for docstring parsing later.
        pass
    return out

