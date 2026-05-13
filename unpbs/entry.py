"""Entry point module for coupling analyzer."""

import math
from collections import Counter, defaultdict
from pathlib import Path

import libcst


class FunctionNode:
    def __init__(self, identifier: str):
        self.identifier = identifier
        self.children: list['FunctionNode'] = []
        self.parents: list['FunctionNode'] = []


class FuncitonCollector(libcst.CSTVisitor):
    def __init__(self) -> None:
        self.functions = []

    def visit_FunctionDef(self, node: libcst.FunctionDef) -> None:
        self.functions.append(node)


class DependencyAnalyzer(libcst.CSTVisitor):
    def __init__(self) -> None:
        self.current_function = None
        self.dependencies: dict[str, set[str]] = defaultdict(set)
        self.function_calls: dict[str, list[str]] = defaultdict(list)

    def rec_visit(self, node) -> None:
        if isinstance(node, tuple):
            for elem in node:
                self.rec_visit(elem)
        elif isinstance(node, libcst.Name):
            # Прямой вызов функции
            if self.current_function:
                self.dependencies[self.current_function].add(node.value)
                self.function_calls[self.current_function].append(node.value)
        elif hasattr(node, "body"):
            self.rec_visit(node.body)
        elif isinstance(node, libcst.Expr):
            self.rec_visit(node.value)
        elif isinstance(node, libcst.Call):
            self.rec_visit(node.func)
        elif isinstance(node, libcst.Attribute):
            # Вызов метода объекта
            if self.current_function:
                method_name = f"{node.value.value}.{node.attr.value}"
                self.dependencies[self.current_function].add(method_name)
                self.function_calls[self.current_function].append(method_name)
        elif isinstance(node, libcst.BinaryOperation):
            self.rec_visit(node.left)
            self.rec_visit(node.right)
        elif isinstance(node, (libcst.If, libcst.For, libcst.While, libcst.With)):
            # Обработка условных конструкций и циклов
            if hasattr(node, "body"):
                self.rec_visit(node.body)
            if hasattr(node, "orelse") and node.orelse:
                self.rec_visit(node.orelse)

    def visit_FunctionDef(self, node: libcst.FunctionDef) -> None:
        self.current_function = node.name.value
        self.rec_visit(node)
        self.current_function = None


def logic(content: str):
    """Анализирует зависимости между функциями и возвращает метрики связанности."""
    tree = libcst.parse_module(content)
    
    # Собираем все функции
    fn_collector = FuncitonCollector()
    tree.visit(fn_collector)
    
    # Анализируем зависимости
    analyzer = DependencyAnalyzer()
    tree.visit(analyzer)
    
    # Создаем результат
    result = {}
    function_names = {
        "file.py::{0}".format(fn.name.value)
        for fn in fn_collector.functions
    }
    
    for fn in function_names:
        fn_name = fn.name.value
        result[fn_name] = {"fan_in": 0, "fan_out": 0}
    
    # Вычисляем fan_out (сколько функций вызывает данная функция)
    for caller, dependencies in analyzer.dependencies.items():
        if caller in function_names:
            result[caller]["fan_out"] = len(dependencies)
    
    # Вычисляем fan_in (сколько раз данная функция вызывается)
    for fn_name in function_names:
        fan_in = 0
        for caller, dependencies in analyzer.dependencies.items():
            if fn_name in dependencies:
                fan_in += 1
        result[fn_name]["fan_in"] = fan_in
    
    return result


def _create_function_nodes(functions: list) -> dict[str, FunctionNode]:
    """Создает узлы графа для всех функций."""
    nodes = {}
    for fn in functions:
        fn_name = fn.name.value
        nodes[fn_name] = FunctionNode(fn_name)
    return nodes


def _build_graph_connections(nodes: dict[str, FunctionNode], dependencies: dict[str, set[str]]) -> None:
    """Строит связи между узлами графа (children/parents)."""
    for caller, deps in dependencies.items():
        if caller in nodes:
            for dep in deps:
                if dep in nodes:
                    # caller зависит от dep
                    nodes[caller].children.append(nodes[dep])
                    nodes[dep].parents.append(nodes[caller])


def _calculate_metrics(nodes: dict[str, FunctionNode]) -> None:
    """Вычисляет метрики fan_in и fan_out для всех узлов."""
    for node in nodes.values():
        node.fan_in = len(node.parents)
        node.fan_out = len(node.children)


def update_node_metrics(node: FunctionNode) -> None:
    """Обновляет метрики для конкретного узла."""
    node.fan_in = len(node.parents)
    node.fan_out = len(node.children)


def get_graph_statistics(nodes: dict[str, FunctionNode]) -> dict[str, int]:
    """Возвращает статистику графа зависимостей."""
    if not nodes:
        return {"total_functions": 0, "max_fan_in": 0, "max_fan_out": 0, "avg_fan_in": 0, "avg_fan_out": 0}
    
    fan_ins = [node.fan_in for node in nodes.values()]
    fan_outs = [node.fan_out for node in nodes.values()]
    
    return {
        "total_functions": len(nodes),
        "max_fan_in": max(fan_ins),
        "max_fan_out": max(fan_outs),
        "avg_fan_in": sum(fan_ins) / len(fan_ins),
        "avg_fan_out": sum(fan_outs) / len(fan_outs)
    }


def build_dependency_graph(content: str) -> dict[str, FunctionNode]:
    """Строит граф зависимостей функций."""
    tree = libcst.parse_module(content)
    
    # Собираем все функции
    fn_collector = FuncitonCollector()
    tree.visit(fn_collector)
    
    # Анализируем зависимости
    analyzer = DependencyAnalyzer()
    tree.visit(analyzer)
    
    # Создаем узлы графа
    nodes = _create_function_nodes(fn_collector.functions)
    
    # Строим связи в графе
    _build_graph_connections(nodes, analyzer.dependencies)
    
    # Вычисляем метрики
    _calculate_metrics(nodes)
    
    return nodes


def visualize_dependency_graph(nodes: dict[str, FunctionNode]) -> str:
    """Создает текстовое представление графа зависимостей."""
    lines = ["Граф зависимостей функций:", "=" * 50]
    
    # Добавляем общую статистику
    stats = get_graph_statistics(nodes)
    lines.append(f"\nОбщая статистика:")
    lines.append(f"  Всего функций: {stats['total_functions']}")
    lines.append(f"  Максимальный fan-in: {stats['max_fan_in']}")
    lines.append(f"  Максимальный fan-out: {stats['max_fan_out']}")
    lines.append(f"  Средний fan-in: {stats['avg_fan_in']:.2f}")
    lines.append(f"  Средний fan-out: {stats['avg_fan_out']:.2f}")
    lines.append("\n" + "=" * 50)
    
    # Сортируем функции по fan-out для лучшей читаемости
    sorted_nodes = sorted(nodes.items(), key=lambda x: x[1].fan_out, reverse=True)
    
    for fn_name, node in sorted_nodes:
        lines.append(f"\nФункция: {fn_name}")
        lines.append(f"  Fan-in: {node.fan_in} (вызывается {node.fan_in} функциями)")
        lines.append(f"  Fan-out: {node.fan_out} (вызывает {node.fan_out} функций)")
        
        if node.children:
            lines.append(f"  Вызывает: {', '.join([child.identifier for child in node.children])}")
        else:
            lines.append("  Вызывает: (нет зависимостей)")
            
        if node.parents:
            lines.append(f"  Вызывается из: {', '.join([parent.identifier for parent in node.parents])}")
        else:
            lines.append("  Вызывается из: (независимая функция)")
    
    return "\n".join(lines)


def decreasing_log(x, base=10, scale=1, shift=1):
    if x == 1:
        return 1
    result = shift + scale - scale * math.log(x, base)
    return max(result, 0.1)


def exponential_growth(x, a=1, b=0.1, max_value=1000):
    result = a * math.exp(b * x)
    return min(result, max_value)


def main() -> None:
    """Main entry point for the application."""
    try:
        # Читаем содержимое файла
        content = Path("file.py").read_text()
        
        # Анализируем зависимости
        print("=== Анализ метрик связанности ===")
        metrics = logic(content)
        for func_name, metrics_data in metrics.items():
            print(f"{func_name}: fan_in={metrics_data['fan_in']}, fan_out={metrics_data['fan_out']}")
        
        print("\n" + "="*60)
        
        # Строим и визуализируем граф зависимостей
        print("=== Граф зависимостей ===")
        nodes = build_dependency_graph(content)
        visualization = visualize_dependency_graph(nodes)
        print(visualization)
        
    except FileNotFoundError:
        print("Ошибка: файл file.py не найден")
    except Exception as e:
        print(f"Ошибка при анализе: {e}")
