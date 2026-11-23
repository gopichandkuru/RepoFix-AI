from dataclasses import dataclass
import math
from pathlib import Path
import re
from typing import Dict, List, Optional, Sequence

from repo_engine.ingest import ingest_directory
from repo_engine.parser import parse_python_file
from repo_engine.symbols import SymbolRecord

_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+")


def tokenize_code(text: str) -> List[str]:
    """Tokenize code/issues while splitting camelCase and snake_case identifiers."""
    tokens: List[str] = []
    for raw in _TOKEN_RE.findall(text):
        lower = raw.lower()
        tokens.append(lower)
        if "_" in lower:
            tokens.extend(part for part in lower.split("_") if part)
        camel_parts = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", raw).lower().split()
        if len(camel_parts) > 1:
            tokens.extend(camel_parts)
    return tokens


@dataclass
class RetrievalCandidate:
    file_path: str
    symbol_name: Optional[str]
    symbol_kind: Optional[str]
    start_line: Optional[int]
    end_line: Optional[int]
    score: float
    exact_symbol_hit: bool = False


class BM25RepoIndex:
    """Lexical BM25 index over repository files and extracted symbols."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_ids: List[str] = []
        self.doc_meta: List[Dict[str, Optional[object]]] = []
        self.doc_tokens: List[List[str]] = []
        self.doc_freqs: List[Dict[str, int]] = []
        self.df: Dict[str, int] = {}
        self.avg_dl: float = 0.0
        self.symbols: List[SymbolRecord] = []

    def index_repository(self, repo_dir: Path) -> None:
        repo_dir = Path(repo_dir).resolve()
        ingested = ingest_directory(repo_dir)

        self.doc_ids.clear()
        self.doc_meta.clear()
        self.doc_tokens.clear()
        self.doc_freqs.clear()
        self.df.clear()
        self.symbols.clear()

        for item in ingested:
            full_path = repo_dir / item.rel_path
            try:
                content = full_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            file_doc_text = f"{item.rel_path}\n{content}"
            self._add_document(
                doc_id=f"file:{item.rel_path}",
                tokens=tokenize_code(file_doc_text),
                meta={
                    "file_path": item.rel_path,
                    "symbol_name": None,
                    "symbol_kind": "file",
                    "start_line": 1,
                    "end_line": max(1, len(content.splitlines())),
                },
            )

            if item.language == "python":
                parsed = parse_python_file(full_path, rel_path=item.rel_path)
                lines = content.splitlines()
                for sym in parsed.symbols:
                    self.symbols.append(sym)
                    snippet = "\n".join(lines[sym.start_line - 1 : sym.end_line])
                    sym_text = f"{item.rel_path} {sym.signature} {snippet}"
                    self._add_document(
                        doc_id=f"sym:{item.rel_path}:{sym.name}:{sym.start_line}",
                        tokens=tokenize_code(sym_text),
                        meta={
                            "file_path": item.rel_path,
                            "symbol_name": sym.name,
                            "symbol_kind": sym.kind,
                            "start_line": sym.start_line,
                            "end_line": sym.end_line,
                        },
                    )

        n_docs = len(self.doc_tokens)
        self.avg_dl = (sum(len(t) for t in self.doc_tokens) / n_docs) if n_docs > 0 else 0.0

    def _add_document(self, doc_id: str, tokens: List[str], meta: Dict[str, Optional[object]]) -> None:
        tf: Dict[str, int] = {}
        for tok in tokens:
            tf[tok] = tf.get(tok, 0) + 1

        self.doc_ids.append(doc_id)
        self.doc_meta.append(meta)
        self.doc_tokens.append(tokens)
        self.doc_freqs.append(tf)

        for tok in tf:
            self.df[tok] = self.df.get(tok, 0) + 1

    def _idf(self, term: str) -> float:
        n_docs = len(self.doc_tokens)
        df_t = self.df.get(term, 0)
        if n_docs == 0 or df_t == 0:
            return 0.0
        # Ensure positive weight even when a term appears in all docs of a tiny corpus
        return max(0.1, math.log(1.0 + (n_docs - df_t + 0.5) / (df_t + 0.5)))

    def search(self, query: str, top_k: int = 5, exact_symbol_boost: float = 2.5) -> List[RetrievalCandidate]:
        q_tokens = tokenize_code(query)
        q_lower_set = {t.lower() for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", query)}
        n_docs = len(self.doc_tokens)
        if n_docs == 0:
            return []

        scored: List[RetrievalCandidate] = []
        for idx in range(n_docs):
            tf_map = self.doc_freqs[idx]
            dl = len(self.doc_tokens[idx])
            denom_norm = self.k1 * (1.0 - self.b + self.b * (dl / max(self.avg_dl, 1e-9)))

            score = 0.0
            for tok in q_tokens:
                f = tf_map.get(tok, 0)
                if f == 0:
                    continue
                idf = self._idf(tok)
                score += idf * ((f * (self.k1 + 1.0)) / (f + denom_norm))

            meta = self.doc_meta[idx]
            fp_str = str(meta["file_path"])
            is_test = Path(fp_str).name.startswith("test_") or "/tests/" in f"/{fp_str}"
            if not is_test and score > 0:
                score += 0.5
            sym_name = meta["symbol_name"]
            exact_hit = False
            if isinstance(sym_name, str) and sym_name.lower() in q_lower_set:
                score += exact_symbol_boost
                exact_hit = True

            scored.append(
                RetrievalCandidate(
                    file_path=str(meta["file_path"]),
                    symbol_name=str(sym_name) if sym_name else None,
                    symbol_kind=str(meta["symbol_kind"]) if meta["symbol_kind"] else None,
                    start_line=int(meta["start_line"]) if meta["start_line"] is not None else None,
                    end_line=int(meta["end_line"]) if meta["end_line"] is not None else None,
                    score=round(score, 4),
                    exact_symbol_hit=exact_hit,
                )
            )

        scored.sort(key=lambda c: (c.score, 1 if c.exact_symbol_hit else 0), reverse=True)
        return scored[:top_k]

    def top_files(self, query: str, top_k: int = 5) -> List[str]:
        candidates = self.search(query, top_k=len(self.doc_ids))
        best_by_file: Dict[str, float] = {}
        for c in candidates:
            if c.file_path not in best_by_file or c.score > best_by_file[c.file_path]:
                best_by_file[c.file_path] = c.score
        ranked = sorted(best_by_file.items(), key=lambda item: item[1], reverse=True)
        return [fp for fp, _ in ranked[:top_k]]


def recall_at_k(ranked_files: Sequence[str], expected_file: str, k: int) -> float:
    return 1.0 if expected_file in ranked_files[:k] else 0.0
