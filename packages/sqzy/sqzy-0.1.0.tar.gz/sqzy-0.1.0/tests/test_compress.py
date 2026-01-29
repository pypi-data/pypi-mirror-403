from __future__ import annotations

import pytest

from sqzy import compress_json, compress_response


def test_compress_json_removes_empty_values() -> None:
    data = {
        "id": 1,
        "name": "  ",
        "description": "",
        "meta": {"page": 1, "next": None, "notes": ""},
        "tags": ["python", "", None, "llm"],
        "empty_list": [],
        "empty_dict": {},
    }

    assert compress_json(data) == {"id": 1, "meta": {"page": 1}, "tags": ["python", "llm"]}


def test_compress_json_preserve_keys() -> None:
    data = {"id": 1, "empty": "", "meta": {"notes": "  "}}
    assert compress_json(data, preserve_keys={"empty", "notes"}) == {
        "id": 1,
        "empty": "",
        "meta": {"notes": "  "},
    }


def test_compress_json_keeps_empty_when_disabled() -> None:
    data = {"name": "   ", "items": [], "meta": {}}
    assert compress_json(
        data,
        drop_empty_str=False,
        drop_whitespace_only=False,
        drop_empty_list=False,
        drop_empty_dict=False,
    ) == data


def test_compress_response_decorator_sync() -> None:
    @compress_response()
    def fetch() -> dict[str, object]:
        return {"id": 1, "name": "", "meta": {"notes": None}}

    assert fetch() == {"id": 1}


@pytest.mark.asyncio
async def test_compress_response_decorator_async() -> None:
    @compress_response()
    async def fetch() -> dict[str, object]:
        return {"id": 1, "name": " ", "meta": {"notes": None}}

    assert await fetch() == {"id": 1}
