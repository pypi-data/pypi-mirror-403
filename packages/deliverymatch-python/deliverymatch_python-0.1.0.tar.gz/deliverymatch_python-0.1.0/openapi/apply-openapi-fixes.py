"""
Fixes DeliveryMatch OpenAPI spec issues that break code generators:
- UUID/method-path operationIds -> snake_case from summary
- Nested $ref to properties -> inline definitions
- Invalid 'byte' content type -> application/octet-stream (binary data)
- Missing parameter names
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Iterator

from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import PlainScalarString

UGLY_ID = re.compile(r"^[a-f0-9]{32}$|^(get|post|put|patch|delete)-")


def iter_operations(spec: dict) -> Iterator[tuple[str, str, dict]]:
    for path, item in spec.get("paths", {}).items():
        for method in ("get", "post", "put", "patch", "delete"):
            if method in item:
                yield path, method, item[method]


def iter_all(node: Any) -> Iterator[tuple[dict, str, Any]]:
    if isinstance(node, dict):
        for key, value in list(node.items()):
            yield node, key, value
            yield from iter_all(value)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            yield node, i, item
            yield from iter_all(item)


def to_snake_case(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\s]", "", s).lower().strip().replace(" ", "_")


def resolve_ref(spec: dict, ref: str) -> dict | None:
    if not ref.startswith("#/"):
        return None
    current = spec
    for part in ref[2:].split("/"):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return dict(current) if isinstance(current, dict) else None


def fix_spec(spec: dict) -> None:
    for _, _, op in iter_operations(spec):
        if op.get("operationId") and op.get("summary"):
            if UGLY_ID.match(op["operationId"]):
                op["operationId"] = PlainScalarString(to_snake_case(op["summary"]))

    for path, item in spec.get("paths", {}).items():
        for method in ("get", "post", "put", "patch", "delete"):
            if method not in item:
                continue
            op = item[method]
            for status, response in op.get("responses", {}).items():
                if isinstance(response, dict) and "content" in response:
                    content = response["content"]
                    if isinstance(content, dict) and "byte" in content:
                        content["application/octet-stream"] = {
                            "schema": {"type": "string", "format": "binary"}
                        }
                        del content["byte"]

    for parent, key, value in iter_all(spec):
        if isinstance(value, dict):
            if "$ref" in value and len(value) == 1 and "/properties/" in value["$ref"]:
                resolved = resolve_ref(spec, value["$ref"])
                if resolved:
                    parent[key] = resolved

            if "in" in value and "name" not in value and "schema" in value:
                value["name"] = "channel"
                value["description"] = "Channel filter"


def main() -> None:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "document_original.yaml")
    dst = Path(sys.argv[2] if len(sys.argv) > 2 else "document.yaml")

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.representer.add_representer(
        type(None),
        lambda self, data: self.represent_scalar("tag:yaml.org,2002:null", "null"),
    )

    with open(src) as f:
        spec = yaml.load(f)

    fix_spec(spec)

    with open(dst, "w") as f:
        yaml.dump(spec, f)

    print(f"Fixed: {src} -> {dst}")


if __name__ == "__main__":
    main()
