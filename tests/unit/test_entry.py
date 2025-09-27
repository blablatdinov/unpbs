"""Unit tests for the entry module."""

from unpbs.entry import logic


def test_logic() -> None:
    """Test the logic function with basic function calls."""
    file_content = "\n".join(
        [
            "def bar():",
            "    return 0",
            "def foo():",
            "    bar()",
        ],
    )
    assert logic(file_content) == {"bar": {"fan_in": 1, "fan_out": 0}, "foo": {"fan_in": 0, "fan_out": 1}}


def test_import() -> None:
    """Test the logic function with import statements."""
    file_content = "\n".join(
        [
            "import httpx",
            "def bar():",
            '    httpx.get("https://example.com")',
        ],
    )
    assert logic(file_content) == {"bar": {"fan_in": 0, "fan_out": 1}}


def test_function() -> None:
    """Test the logic function with multiple function calls."""
    file_content = "\n".join(
        [
            "def foo():",
            "    pass",
            "def bar():",
            "    foo()",
            "    baz()",
            "def baz():",
            "    bizz()",
            "def bizz():",
            "    pass",
        ],
    )
    assert logic(file_content) == {
        "foo": {"fan_in": 1, "fan_out": 0},
        "bar": {"fan_in": 0, "fan_out": 2},
        "baz": {"fan_in": 1, "fan_out": 1},
        "bizz": {"fan_in": 1, "fan_out": 0},
    }


def test_without_call() -> None:
    """Test the logic function with function references without calls."""
    file_content = "\n".join(
        [
            "def foo():",
            "    pass",
            "def bar():",
            "    foo",
        ],
    )
    assert logic(file_content) == {"foo": {"fan_in": 1, "fan_out": 0}, "bar": {"fan_in": 0, "fan_out": 1}}
