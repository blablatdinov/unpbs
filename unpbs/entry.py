"""Entry point module for coupling analyzer."""

import math
from collections import Counter, defaultdict
from pathlib import Path

import libcst


class FuncitonCollector(libcst.CSTVisitor):
    def __init__(self) -> None:
        self.functions = []

    def visit_FunctionDef(self, node: libcst.FunctionDef) -> None:
        self.functions.append(node)


class FunctionUsages(libcst.CSTVisitor):
    def __init__(self, analyze_fn) -> None:
        self.current_function = None
        self.analyze_fn = analyze_fn
        self.usages: dict[str, set[str]] = defaultdict(list)

    def rec_visit(self, node) -> None:
        if isinstance(node, tuple):
            for elem in node:
                self.rec_visit(elem)
        if isinstance(node, libcst.Name) and node.value == self.analyze_fn:
            self.usages[self.analyze_fn].append(self.current_function)
        if hasattr(node, "body"):
            self.rec_visit(node.body)
        if isinstance(node, libcst.Expr):
            self.rec_visit(node.value)
        if isinstance(node, libcst.Call):
            self.rec_visit(node.func)
        if isinstance(node, libcst.Attribute):
            self.usages[node.value.value + "." + node.attr.value].append(self.analyze_fn)
        if isinstance(node, libcst.BinaryOperation):
            self.rec_visit(node.left)
            self.rec_visit(node.right)

    def visit_FunctionDef(self, node: libcst.FunctionDef) -> None:
        self.current_function = node.name.value
        self.rec_visit(node)
        self.current_function = None


def logic(content: str):
    tree = libcst.parse_module(content)
    fn_cltr = FuncitonCollector()
    tree.visit(fn_cltr)
    result = {key.name.value: {"fan_in": 0, "fan_out": 0} for key in fn_cltr.functions}
    for fn in fn_cltr.functions:
        fn_usages = FunctionUsages(fn.name.value)
        tree.visit(fn_usages)
        for func, usages in fn_usages.usages.items():
            for usg, usg_cnt in Counter(usages).items():
                result[usg]["fan_out"] += round(decreasing_log(usg_cnt), 2)
            if result.get(func):
                result[func]["fan_in"] = len(set(usages))
    return result


def decreasing_log(x, base=10, scale=1, shift=1):
    if x == 1:
        return 1
    result = shift + scale - scale * math.log(x, base)
    return max(result, 0.1)


def main() -> None:
    """Main entry point for the application."""
    # TODO #1:30min replace `file.py` with file name from args
    # TODO #1:30min try/except for all cases
    print(logic(Path("file.py").read_text()))  # noqa: T201
