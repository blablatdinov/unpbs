"""Unit tests for the entry module."""

from unpbs.entry import (
    logic, 
    build_dependency_graph, 
    visualize_dependency_graph,
    update_node_metrics,
    get_graph_statistics
)


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


def test_double_usage() -> None:
    file_content = "\n".join(
        [
            "def bar():",
            "    return 0",
            "def foo():",
            "    bar() + bar()",
        ],
    )
    assert logic(file_content) == {"bar": {"fan_in": 1, "fan_out": 0}, "foo": {"fan_in": 0, "fan_out": 1}}


def test_combine_usage() -> None:
    file_content = "\n".join(
        [
            "def bar():",
            "    return 0",
            "def baz():",
            "    return 0",
            "def foo():",
            "    baz()",
            "    bar() + bar()",
        ],
    )
    assert logic(file_content) == {
        "bar": {"fan_in": 1, "fan_out": 0},
        "baz": {"fan_in": 1, "fan_out": 0},
        "foo": {"fan_in": 0, "fan_out": 2},
    }


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


def test_depth_usage() -> None:
    file_content = "\n".join(
        [
            "def bar():",
            "    return 0",
            "def foo():",
            "	bar()",
            "def baz():",
            "	foo()",
            "def main():",
            "	baz()",
        ],
    )
    assert logic(file_content) == {
        "bar": {"fan_in": 1, "fan_out": 0}, 
        "foo": {"fan_in": 1, "fan_out": 1}, 
        "baz": {"fan_in": 1, "fan_out": 1}, 
        "main": {"fan_in": 0, "fan_out": 1}
    }


def test_build_dependency_graph() -> None:
    """Test building dependency graph."""
    file_content = "\n".join(
        [
            "def bar():",
            "    return 0",
            "def foo():",
            "    bar()",
        ],
    )
    nodes = build_dependency_graph(file_content)
    
    assert "bar" in nodes
    assert "foo" in nodes
    
    # foo зависит от bar
    assert nodes["foo"].children[0].identifier == "bar"
    assert nodes["bar"].parents[0].identifier == "foo"
    
    # Проверяем метрики
    assert nodes["foo"].fan_out == 1  # foo вызывает 1 функцию
    assert nodes["foo"].fan_in == 0   # foo не вызывается
    assert nodes["bar"].fan_out == 0  # bar не вызывает функций
    assert nodes["bar"].fan_in == 1   # bar вызывается 1 раз


def test_visualize_dependency_graph() -> None:
    """Test dependency graph visualization."""
    file_content = "\n".join(
        [
            "def bar():",
            "    return 0",
            "def foo():",
            "    bar()",
        ],
    )
    nodes = build_dependency_graph(file_content)
    visualization = visualize_dependency_graph(nodes)
    
    assert "Граф зависимостей функций:" in visualization
    assert "Функция: bar" in visualization
    assert "Функция: foo" in visualization
    assert "Fan-in: 0" in visualization
    assert "Fan-out: 1" in visualization


def test_complex_dependency_graph() -> None:
    """Test complex dependency graph with multiple functions."""
    file_content = "\n".join(
        [
            "def a():",
            "    pass",
            "def b():",
            "    a()",
            "def c():",
            "    a()",
            "    b()",
        ],
    )
    nodes = build_dependency_graph(file_content)
    
    # Проверяем структуру графа
    assert len(nodes["a"].parents) == 2  # a вызывается из b и c
    assert len(nodes["b"].parents) == 1  # b вызывается из c
    assert len(nodes["c"].parents) == 0  # c не вызывается
    
    assert len(nodes["a"].children) == 0  # a не вызывает функций
    assert len(nodes["b"].children) == 1  # b вызывает a
    assert len(nodes["c"].children) == 2  # c вызывает a и b
    
    # Проверяем метрики
    assert nodes["a"].fan_in == 2
    assert nodes["a"].fan_out == 0
    assert nodes["b"].fan_in == 1
    assert nodes["b"].fan_out == 1
    assert nodes["c"].fan_in == 0
    assert nodes["c"].fan_out == 2


def test_update_node_metrics() -> None:
    """Test updating metrics for a single node."""
    file_content = "\n".join(
        [
            "def a():",
            "    pass",
            "def b():",
            "    a()",
        ],
    )
    nodes = build_dependency_graph(file_content)
    
    # Проверяем, что метрики уже рассчитаны
    assert nodes["a"].fan_in == 1
    assert nodes["a"].fan_out == 0
    
    # Обновляем метрики для узла a
    update_node_metrics(nodes["a"])
    assert nodes["a"].fan_in == 1
    assert nodes["a"].fan_out == 0


def test_get_graph_statistics() -> None:
    """Test graph statistics calculation."""
    file_content = "\n".join(
        [
            "def a():",
            "    pass",
            "def b():",
            "    a()",
            "def c():",
            "    a()",
            "    b()",
        ],
    )
    nodes = build_dependency_graph(file_content)
    stats = get_graph_statistics(nodes)
    
    assert stats["total_functions"] == 3
    assert stats["max_fan_in"] == 2  # a вызывается 2 раза
    assert stats["max_fan_out"] == 2  # c вызывает 2 функции
    assert stats["avg_fan_in"] == 1.0  # (2+1+0)/3
    assert stats["avg_fan_out"] == 1.0  # (0+1+2)/3


def test_get_graph_statistics_empty() -> None:
    """Test graph statistics for empty graph."""
    stats = get_graph_statistics({})
    
    assert stats["total_functions"] == 0
    assert stats["max_fan_in"] == 0
    assert stats["max_fan_out"] == 0
    assert stats["avg_fan_in"] == 0
    assert stats["avg_fan_out"] == 0
