from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, List, Optional, Sequence, Tuple, Type, TypeVar, Union, cast

T = TypeVar("T")


@dataclass(frozen=True)
class StructuredResult(Generic[T]):
    """
    Koog-parity structured output result container.

    Kotlin reference: `StructuredLLMResponse` / structured parsing + optional fixing retries.
    """

    ok: bool
    value: Optional[T] = None
    error: Optional[str] = None
    raw: Any = None
    # Best-effort: original assistant text that was parsed.
    text: Optional[str] = None


@dataclass(frozen=True)
class JsonSchema:
    """
    Koog-like JSON schema wrapper.

    Kotlin reference: `LLMParams.Schema.JSON.Basic` / `LLMParams.Schema.JSON.Standard`.
    In Python parity, callers can supply either:
    - JsonSchema(name=..., schema={...})
    - raw schema dict (treated as Standard flavor)
    """

    name: str
    schema: Dict[str, Any]
    # If true, validation will reject unknown properties when schema says additionalProperties=false.
    strict: bool = True


@dataclass(frozen=True)
class StructureFixingParser:
    """
    Koog-like structure fixing parser.

    Kotlin reference: `StructureFixingParser(model=..., retries=...)`.
    """

    model: Any
    retries: int = 3


def _json_dumps_pretty(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)


_CODE_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


def extract_json_payload(text: str) -> str:
    """
    Extract a JSON object/array payload from a model response.

    Handles:
    - fenced ```json ... ```
    - bare JSON mixed with prose
    """
    t = (text or "").strip()
    if not t:
        return ""

    m = _CODE_FENCE_RE.search(t)
    if m:
        inner = (m.group(1) or "").strip()
        if inner:
            t = inner

    # If the entire string parses as JSON, prefer that.
    try:
        json.loads(t)
        return t
    except Exception:
        pass

    # Heuristic: locate first "{" or "[" and match the last "}" or "]".
    starts = [(t.find("{"), "{", "}"), (t.find("["), "[", "]")]
    starts = [x for x in starts if x[0] != -1]
    if not starts:
        return t
    starts.sort(key=lambda x: x[0])
    i0, open_ch, close_ch = starts[0]
    i1 = t.rfind(close_ch)
    if i1 == -1 or i1 <= i0:
        return t[i0:].strip()
    return t[i0 : i1 + 1].strip()


def _type_name(v: Any) -> str:
    return type(v).__name__


def _validate_schema(value: Any, schema: Dict[str, Any], *, path: str = "$") -> List[str]:
    """
    Minimal JSON-schema validator covering the schema shapes we use in Koog tools/prompts:
    - type: object/array/string/number/integer/boolean/null
    - properties + required + additionalProperties
    - items
    - enum
    - oneOf/anyOf/allOf
    """
    errors: List[str] = []
    if not isinstance(schema, dict):
        return [f"{path}: schema must be an object, got {_type_name(schema)}"]

    if "enum" in schema:
        enum = schema.get("enum")
        if isinstance(enum, list) and value not in enum:
            errors.append(f"{path}: expected one of {enum!r}, got {value!r}")
            return errors

    # Combinators
    for key in ("oneOf", "anyOf"):
        if key in schema and isinstance(schema.get(key), list):
            subs = cast(List[Any], schema.get(key))
            ok_any = False
            sub_errors: List[str] = []
            for idx, sub in enumerate(subs):
                errs = _validate_schema(value, sub if isinstance(sub, dict) else {}, path=path)
                if not errs:
                    ok_any = True
                    break
                sub_errors.append(f"{path}: {key}[{idx}] failed: {errs[0]}")
            if not ok_any:
                errors.extend(sub_errors or [f"{path}: {key} did not match any branch"])
            return errors

    if "allOf" in schema and isinstance(schema.get("allOf"), list):
        subs = cast(List[Any], schema.get("allOf"))
        for idx, sub in enumerate(subs):
            errors.extend(_validate_schema(value, sub if isinstance(sub, dict) else {}, path=path))
        return errors

    t = schema.get("type")
    if t is None:
        # No type specified -> accept anything.
        return errors

    if t == "object":
        if not isinstance(value, dict):
            return [f"{path}: expected object, got {_type_name(value)}"]
        props_raw = schema.get("properties")
        props: Dict[str, Any] = props_raw if isinstance(props_raw, dict) else {}
        required_raw = schema.get("required")
        required_list: List[Any] = list(required_raw) if isinstance(required_raw, list) else []
        required_set = {str(x) for x in required_list}
        for rk in sorted(required_set):
            if rk not in value:
                errors.append(f"{path}: missing required property {rk!r}")
        for k, v in value.items():
            if k in props:
                sub = props.get(k)
                if isinstance(sub, dict):
                    errors.extend(_validate_schema(v, sub, path=f"{path}.{k}"))
            else:
                ap = schema.get("additionalProperties", True)
                if ap is False:
                    errors.append(f"{path}: unexpected property {k!r}")
                elif isinstance(ap, dict):
                    errors.extend(_validate_schema(v, ap, path=f"{path}.{k}"))
        return errors

    if t == "array":
        if not isinstance(value, list):
            return [f"{path}: expected array, got {_type_name(value)}"]
        items = schema.get("items")
        if isinstance(items, dict):
            for i, v in enumerate(value):
                errors.extend(_validate_schema(v, items, path=f"{path}[{i}]"))
        return errors

    if t == "string":
        return [] if isinstance(value, str) else [f"{path}: expected string, got {_type_name(value)}"]
    if t == "integer":
        return [] if isinstance(value, int) and not isinstance(value, bool) else [f"{path}: expected integer, got {_type_name(value)}"]
    if t == "number":
        return [] if isinstance(value, (int, float)) and not isinstance(value, bool) else [f"{path}: expected number, got {_type_name(value)}"]
    if t == "boolean":
        return [] if isinstance(value, bool) else [f"{path}: expected boolean, got {_type_name(value)}"]
    if t == "null":
        return [] if value is None else [f"{path}: expected null, got {_type_name(value)}"]

    # Unknown type string -> accept.
    return errors


def _make_structured_system_instructions(*, schema: JsonSchema, examples: Optional[Sequence[Any]] = None) -> str:
    """
    Prompt-injection strategy (works across models/endpoints).
    Koog uses model capabilities to prefer native, but will inject when needed.
    """
    parts: List[str] = []
    parts.append("You MUST reply with a single valid JSON value that matches the schema below.")
    parts.append("Do not include markdown, code fences, comments, or any extra keys.")
    parts.append("")
    parts.append("JSON Schema (for validation):")
    parts.append(_json_dumps_pretty({"name": schema.name, "schema": schema.schema}))
    if examples:
        parts.append("")
        parts.append("Examples (do not copy verbatim; follow the structure):")
        try:
            parts.append(_json_dumps_pretty(list(examples)))
        except Exception:
            # Examples are best-effort.
            pass
    return "\n".join(parts).strip()


def parse_structured_json(
    *,
    assistant_text: str,
    schema: Union[JsonSchema, Dict[str, Any]],
) -> Tuple[Optional[Any], Optional[str]]:
    """
    Parse + minimally validate JSON from assistant text.
    Returns (value, error).
    """
    jschema: JsonSchema
    if isinstance(schema, JsonSchema):
        jschema = schema
    else:
        jschema = JsonSchema(name="schema", schema=dict(schema or {}), strict=True)

    payload = extract_json_payload(assistant_text)
    if not payload:
        return None, "Empty response; expected JSON."
    try:
        value = json.loads(payload)
    except Exception as e:
        return None, f"JSON parse error: {e}"

    errs = _validate_schema(value, jschema.schema, path="$")
    if errs:
        return None, "Schema validation failed: " + "; ".join(errs[:5])
    return value, None


def execute_structured(
    *,
    llm: Any,
    prompt: Any,
    schema: Union[JsonSchema, Dict[str, Any]],
    examples: Optional[Sequence[Any]] = None,
    fixing_parser: Optional[StructureFixingParser] = None,
    decode: Optional[Callable[[Any], T]] = None,
    model: Any = None,
    params: Optional[Dict[str, Any]] = None,
) -> StructuredResult[T]:
    """
    Koog-parity structured output helper (session/executor layer).

    - Works with any `LLMExecutor`-like object exposing `.invoke(...)` (this package's LLMExecutor).
    - Uses prompt-injection + JSON parsing + minimal schema validation.
    - If `fixing_parser` is provided, retries by asking a fixing model to output corrected JSON.
    """
    from .llm_executor import ToolChoice  # local import to avoid cycles
    from .messages import AssistantMessage, Prompt, SystemMessage, UserMessage

    base_prompt: Prompt = prompt if isinstance(prompt, Prompt) else Prompt()

    jschema: JsonSchema = schema if isinstance(schema, JsonSchema) else JsonSchema(name="schema", schema=dict(schema or {}), strict=True)

    def _call_once(p: Prompt, *, use_model: Any, use_params: Dict[str, Any]) -> Tuple[Optional[str], Any]:
        resp = llm.invoke(p, tool_choice=ToolChoice.NONE, model=use_model, params=use_params)
        txt = next((m.text for m in resp.responses if isinstance(m, AssistantMessage)), None)
        return txt, resp.raw

    effective_model = model
    effective_params = dict(params or {})

    # Inject instructions as an extra system message.
    injected = Prompt(messages=list(base_prompt.messages))
    injected.append(SystemMessage(text=_make_structured_system_instructions(schema=jschema, examples=examples)))

    txt, raw = _call_once(injected, use_model=effective_model, use_params=effective_params)
    if txt is None:
        return StructuredResult(ok=False, error="LLM returned no assistant text.", raw=raw, text=None)

    value, err = parse_structured_json(assistant_text=txt, schema=jschema)
    if err is None:
        try:
            outv: Any = value
            if decode is not None:
                outv = decode(value)
            return StructuredResult(ok=True, value=cast(T, outv), raw=raw, text=txt)
        except Exception as e:
            return StructuredResult(ok=False, error=f"Decode error: {e}", raw=raw, text=txt)

    # Optional fixing retries
    fp = fixing_parser
    if fp is None or fp.retries <= 0:
        return StructuredResult(ok=False, error=err, raw=raw, text=txt)

    last_err = err
    last_txt = txt
    last_raw = raw
    for _ in range(fp.retries):
        fix_prompt = Prompt(messages=list(base_prompt.messages))
        fix_prompt.append(
            SystemMessage(
                text=(
                    "You are a JSON fixing assistant. Return ONLY valid JSON that matches the provided schema.\n"
                    "Do not include markdown or extra text."
                )
            )
        )
        fix_prompt.append(UserMessage(text="Schema:\n" + _json_dumps_pretty(jschema.schema)))
        fix_prompt.append(UserMessage(text="Invalid JSON output:\n" + (last_txt or "")))
        fix_prompt.append(UserMessage(text="Error:\n" + (last_err or "")))
        txt2, raw2 = _call_once(fix_prompt, use_model=fp.model, use_params=effective_params)
        last_raw = raw2
        if txt2 is None:
            last_err = "Fixing model returned no assistant text."
            continue
        last_txt = txt2
        value2, err2 = parse_structured_json(assistant_text=txt2, schema=jschema)
        if err2 is None:
            try:
                outv2: Any = value2
                if decode is not None:
                    outv2 = decode(value2)
                return StructuredResult(ok=True, value=cast(T, outv2), raw=raw2, text=txt2)
            except Exception as e:
                return StructuredResult(ok=False, error=f"Decode error: {e}", raw=raw2, text=txt2)
        last_err = err2

    return StructuredResult(ok=False, error=last_err, raw=last_raw, text=last_txt)

