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
    assert logic(file_content) == "\n".join(
        [
            "bar",
            "  fan_in: 1",
            "  fan_out: 0",
            "foo",
            "  fan_in: 0",
            "  fan_out: 1",
        ],
    )


def test_import() -> None:
    """Test the logic function with import statements."""
    file_content = "\n".join(
        [
            "import httpx",
            "def bar():",
            '    httpx.get("https://example.com")',
        ],
    )
    assert logic(file_content) == "\n".join(
        [
            "bar",
            "  fan_in: 0",
            "  fan_out: 0",
        ],
    )
