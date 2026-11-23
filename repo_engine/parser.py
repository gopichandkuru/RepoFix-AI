import ast
from pathlib import Path
from typing import List, Optional

from repo_engine.symbols import ParsedFile, SymbolRecord


def _format_args(args: ast.arguments) -> str:
    parts = [a.arg for a in getattr(args, "posonlyargs", [])]
    parts.extend(a.arg for a in args.args)
    if args.vararg:
        parts.append("*" + args.vararg.arg)
    elif args.kwonlyargs:
        parts.append("*")
    parts.extend(a.arg for a in args.kwonlyargs)
    if args.kwarg:
        parts.append("**" + args.kwarg.arg)
    return ", ".join(parts)


def _extract_calls(node: ast.AST) -> List[str]:
    calls: List[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                calls.append(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                calls.append(child.func.attr)
    # Preserve order while deduplicating
    return list(dict.fromkeys(calls))


def parse_python_source(source: str, file_path: str) -> ParsedFile:
    parsed = ParsedFile(file_path=file_path, language="python")
    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError as exc:
        parsed.parse_error = f"SyntaxError at line {exc.lineno}: {exc.msg}"
        return parsed

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                parsed.imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                full = f"{module}.{alias.name}" if module else alias.name
                parsed.imports.append(full)

    parsed.imports = list(dict.fromkeys(parsed.imports))

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            kind = "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function"
            end_line = getattr(node, "end_lineno", node.lineno) or node.lineno
            parsed.symbols.append(
                SymbolRecord(
                    name=node.name,
                    kind=kind,
                    file_path=file_path,
                    start_line=node.lineno,
                    end_line=end_line,
                    parent=None,
                    signature=f"{node.name}({_format_args(node.args)})",
                    calls=_extract_calls(node),
                )
            )
        elif isinstance(node, ast.ClassDef):
            cls_end = getattr(node, "end_lineno", node.lineno) or node.lineno
            parsed.symbols.append(
                SymbolRecord(
                    name=node.name,
                    kind="class",
                    file_path=file_path,
                    start_line=node.lineno,
                    end_line=cls_end,
                    parent=None,
                    signature=f"class {node.name}",
                    calls=[],
                )
            )
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    m_end = getattr(item, "end_lineno", item.lineno) or item.lineno
                    parsed.symbols.append(
                        SymbolRecord(
                            name=item.name,
                            kind="method",
                            file_path=file_path,
                            start_line=item.lineno,
                            end_line=m_end,
                            parent=node.name,
                            signature=f"{node.name}.{item.name}({_format_args(item.args)})",
                            calls=_extract_calls(item),
                        )
                    )

    return parsed


def parse_python_file(path: Path, rel_path: Optional[str] = None) -> ParsedFile:
    path = Path(path)
    label = rel_path or path.as_posix()
    source = path.read_text(encoding="utf-8", errors="replace")
    return parse_python_source(source, file_path=label)
