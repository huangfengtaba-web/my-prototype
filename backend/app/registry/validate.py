# -*- coding: utf-8 -*-
"""轻量 JSON Schema 校验器。

只支持我们实际用到的 draft-07 子集：
  type / properties / required / enum / minimum / maximum / minLength / maxLength /
  default / additionalProperties / items

不引入 jsonschema 依赖（保持项目零重型依赖）。
"""
from typing import Any

_TYPES = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "object": dict,
    "array": list,
}


def validate(value: Any, schema: dict, path: str = "") -> list[str]:
    """返回错误信息列表；空列表表示通过。"""
    errors: list[str] = []
    if not schema:
        return errors

    t = schema.get("type")
    if t and t in _TYPES:
        expected = _TYPES[t]
        # bool 是 int 的子类，需单独排除，否则 True 会被当成整数通过
        if t in ("integer", "number") and isinstance(value, bool):
            errors.append(f"{path or 'value'} 应为 {t}，实际为 boolean")
            return errors
        if not isinstance(value, expected):
            errors.append(f"{path or 'value'} 应为 {t}，实际为 {type(value).__name__}")
            return errors

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path or 'value'} 必须是 {schema['enum']} 之一，实际为 {value!r}")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path} 长度不得小于 {schema['minLength']}")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path} 长度不得大于 {schema['maxLength']}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path} 不得小于 {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path} 不得大于 {schema['maximum']}")

    if isinstance(value, dict):
        props = schema.get("properties") or {}
        for req in schema.get("required") or []:
            if req not in value or value[req] is None:
                errors.append(f"缺少必填参数 {path + '.' if path else ''}{req}")
        if schema.get("additionalProperties") is False:
            extra = [k for k in value if k not in props]
            if extra:
                errors.append(f"存在未定义参数: {', '.join(extra)}")
        for k, v in value.items():
            if k in props and v is not None:
                errors.extend(validate(v, props[k], f"{path + '.' if path else ''}{k}"))

    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            errors.extend(validate(item, schema["items"], f"{path}[{i}]"))

    return errors


def validate_args(skill, args: dict | None) -> list[str]:
    """按 skill.input_schema 校验实参。"""
    return validate(args or {}, skill.input_schema)


__all__ = ["validate", "validate_args"]
