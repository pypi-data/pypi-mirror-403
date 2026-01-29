# prompt-blueprint-validator

Validate “Prompt Blueprint” JSON against a schema.

Homepage: https://aigeeza.com/tools/blueprint-builder  
Schema repo: https://github.com/tallwhites/prompt-blueprint-schema

## Install
```bash
pip install prompt-blueprint-validator
```

## Usage
```bash
pbv-py path/to/blueprint.json
```

Exit codes:
- 0 = OK
- 2 = validation errors
