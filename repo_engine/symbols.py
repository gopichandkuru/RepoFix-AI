from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SymbolRecord:
    name: str
    kind: str  # "function" | "async_function" | "class" | "method"
    file_path: str
    start_line: int
    end_line: int
    parent: Optional[str] = None
    signature: str = ""
    calls: List[str] = field(default_factory=list)


@dataclass
class ParsedFile:
    file_path: str
    language: str
    symbols: List[SymbolRecord] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    parse_error: Optional[str] = None
