from pathlib import Path

from repo_engine.parser import parse_python_file, parse_python_source


def test_parse_fixture_symbols():
    fixture_file = Path("datasets/curated/fixtures/fix_01_discount/repo/shop/pricing.py")
    parsed = parse_python_file(fixture_file, rel_path="shop/pricing.py")

    assert parsed.parse_error is None
    assert [s.name for s in parsed.symbols] == ["apply_discount"]
    assert parsed.symbols[0].kind == "function"
    assert parsed.symbols[0].start_line == 1


def test_parse_class_method_and_imports():
    code = """
import os
from typing import List

class OrderService:
    def compute_total(self, prices: List[float]) -> float:
        return sum(prices)
"""
    parsed = parse_python_source(code, file_path="orders.py")
    assert parsed.parse_error is None
    assert "os" in parsed.imports
    assert "typing.List" in parsed.imports

    by_name = {s.name: s for s in parsed.symbols}
    assert by_name["OrderService"].kind == "class"
    assert by_name["compute_total"].kind == "method"
    assert by_name["compute_total"].parent == "OrderService"
    assert "sum" in by_name["compute_total"].calls


def test_parse_handles_syntax_error_gracefully():
    bad_code = "def broken(:\n    pass\n"
    parsed = parse_python_source(bad_code, file_path="bad.py")
    assert parsed.parse_error is not None
    assert parsed.symbols == []
