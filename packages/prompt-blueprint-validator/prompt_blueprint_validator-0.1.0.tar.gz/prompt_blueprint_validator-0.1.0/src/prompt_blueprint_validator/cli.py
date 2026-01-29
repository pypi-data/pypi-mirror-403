import json
import sys
from importlib.resources import files
from jsonschema import Draft202012Validator


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: pbv-py <file.json>")
        return 1

    schema_text = files("prompt_blueprint_validator").joinpath(
        "schema/prompt-blueprint.schema.json"
    ).read_text(encoding="utf-8")
    schema = json.loads(schema_text)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)

    v = Draft202012Validator(schema)
    errors = list(v.iter_errors(data))

    if not errors:
        print("OK")
        return 0

    for e in errors:
        print(e.message)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
