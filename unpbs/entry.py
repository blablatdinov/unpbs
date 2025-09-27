"""Entry point module for coupling analyzer."""

from pathlib import Path

import libcst


def find_function_calls(tree: libcst.Module) -> dict[str, set[str]]:
    """Find function calls within a module AST."""
    function_calls: dict[str, set[str]] = {}
    defined_functions: set[str] = set()

    class FunctionCollector(libcst.CSTVisitor):
        def visit_FunctionDef(self, node: libcst.FunctionDef) -> bool:  # noqa: N802
            defined_functions.add(node.name.value)
            return True

    collector = FunctionCollector()
    tree.visit(collector)

    class FunctionCallVisitor(libcst.CSTVisitor):
        def __init__(self) -> None:
            self.current_function: str | None = None
            self.calls: set[str] = set()
            self.in_function_def = False

        def visit_FunctionDef(self, node: libcst.FunctionDef) -> bool:  # noqa: N802
            self.current_function = node.name.value
            self.calls = set()
            self.in_function_def = True
            return True

        def leave_FunctionDef(self, node: libcst.FunctionDef) -> None:  # noqa: N802
            if self.current_function:
                function_calls[self.current_function] = self.calls.copy()
                self.current_function = None
                self.calls = set()
            self.in_function_def = False
        
        def visit_FunctionDef_body(self, node: libcst.FunctionDef) -> None:  # noqa: N802
            # Когда входим в тело функции, сбрасываем флаг
            self.in_function_def = False

        def visit_Call(self, node: libcst.Call) -> bool:  # noqa: N802
            if self.current_function:
                # Учитываем вызовы функций, определенных в модуле
                if isinstance(node.func, libcst.Name) and node.func.value in defined_functions:
                    self.calls.add(node.func.value)
                # Учитываем вызовы методов объектов (например, httpx.get)
                elif isinstance(node.func, libcst.Attribute):
                    # Добавляем имя метода как вызов
                    self.calls.add(node.func.attr.value)
            return True
        
        def visit_Name(self, node: libcst.Name) -> bool:
            # Учитываем простые ссылки на функции (без вызова), но не в определениях функций
            if (self.current_function and 
                not self.in_function_def and 
                node.value in defined_functions):
                self.calls.add(node.value)
            return True

    visitor = FunctionCallVisitor()
    tree.visit(visitor)
    return function_calls


def calculate_fanin_fanout(function_calls: dict[str, set[str]]) -> dict[str, dict[str, int]]:
    """Calculate fan-in and fan-out metrics for functions."""
    results = {}
    for func_name, calls in function_calls.items():
        results[func_name] = {"fan_in": 0, "fan_out": len(calls)}
    for called_functions in function_calls.values():
        for called_func in called_functions:
            if called_func in results:
                results[called_func]["fan_in"] += 1
    return results


def logic(file_content: str) -> dict[str, dict[str, int]]:
    """Analyze coupling metrics for given file content."""
    tree = libcst.parse_module(file_content)
    function_calls = find_function_calls(tree)
    return calculate_fanin_fanout(function_calls)


def main() -> None:
    """Main entry point for the application."""
    # TODO #1:30min replace `file.py` with file name from args
    # TODO #1:30min try/except for all cases
    print(logic(Path("file.py").read_text()))  # noqa: T201
