"""Entry point module for coupling analyzer."""

import libcst
from pathlib import Path


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

        def visit_FunctionDef(self, node: libcst.FunctionDef) -> bool:  # noqa: N802
            self.current_function = node.name.value
            self.calls = set()
            return True

        def leave_FunctionDef(self, node: libcst.FunctionDef) -> None:  # noqa: N802
            if self.current_function:
                function_calls[self.current_function] = self.calls.copy()
                self.current_function = None
                self.calls = set()

        def visit_Call(self, node: libcst.Call) -> bool:  # noqa: N802
            if self.current_function and isinstance(node.func, libcst.Name) and node.func.value in defined_functions:
                self.calls.add(node.func.value)
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


def logic(file_content: str) -> str:
    """Analyze coupling metrics for given file content."""
    tree = libcst.parse_module(file_content)
    function_calls = find_function_calls(tree)
    results = calculate_fanin_fanout(function_calls)
    output = []
    for func_name, metrics in results.items():
        output.append(f"{func_name}")
        output.append(f"  fan_in: {metrics['fan_in']}")
        output.append(f"  fan_out: {metrics['fan_out']}")
    return "\n".join(output)


def main() -> None:
    """Main entry point for the application."""
    # TODO #1:30min replace `file.py` with file name from args
    # TODO #1:30min try/except for all cases
    print(logic(Path("file.py").read_text()))
