# Sqzy

Sqzy removes irrelevant fields from JSON-like API responses before you send
them to LLMs. It drops nulls, blanks, and empty collections so the context
window is used for meaningful data.

## Install

```bash
pip install sqzy
```

## Quick start

```python
from sqzy import compress_json, compress_response

data = {
    "id": 123,
    "title": "  ",
    "summary": None,
    "tags": ["python", "", None, "llm"],
    "meta": {"page": 1, "next": None, "notes": ""},
}

print(compress_json(data))
# {'id': 123, 'tags': ['python', 'llm'], 'meta': {'page': 1}}
```

Decorator usage:

```python
import requests
from sqzy import compress_response

@compress_response()
def fetch_user(user_id: str):
    res = requests.get(f"https://api.example.com/users/{user_id}")
    return res.json()

clean = fetch_user("42")
```

## API

`compress_json(data, **options)` recursively removes:
- `None` values
- empty strings (including whitespace-only by default)
- empty lists and dicts

`compress_response(**options)` is a decorator that applies `compress_json` to
the return value of the wrapped function.

### Options

- `drop_null` (bool): remove `None` values (default `True`)
- `drop_empty_str` (bool): remove empty strings (default `True`)
- `drop_whitespace_only` (bool): remove strings with only whitespace (default `True`)
- `drop_empty_list` (bool): remove empty lists (default `True`)
- `drop_empty_dict` (bool): remove empty dicts (default `True`)
- `preserve_keys` (set[str] or list[str]): keep values for specific keys

## Contributing

Issues and pull requests are welcome. See `CONTRIBUTING.md` for local setup.
