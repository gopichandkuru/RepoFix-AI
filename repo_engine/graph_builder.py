from pathlib import Path
from typing import Dict, List
import networkx as nx

from repo_engine.ingest import ingest_directory
from repo_engine.parser import parse_python_file


def _is_test_file(rel_path: str) -> bool:
    p = Path(rel_path)
    return p.name.startswith("test_") or "/tests/" in f"/{rel_path}" or rel_path.startswith("tests/")


class RepoGraphBuilder:
    """Builds a lightweight NetworkX code graph of files, symbols, imports, calls, and tests."""

    def __init__(self):
        self.graph = nx.DiGraph()

    def build_from_repo(self, repo_dir: Path) -> nx.DiGraph:
        repo_dir = Path(repo_dir).resolve()
        self.graph.clear()
        ingested = ingest_directory(repo_dir)

        symbol_nodes_by_name: Dict[str, List[str]] = {}
        parsed_by_file = {}

        for item in ingested:
            file_node = f"file:{item.rel_path}"
            node_type = "test" if _is_test_file(item.rel_path) else "file"
            self.graph.add_node(
                file_node,
                node_type=node_type,
                file_path=item.rel_path,
                language=item.language,
            )

            if item.language == "python":
                parsed = parse_python_file(repo_dir / item.rel_path, rel_path=item.rel_path)
                parsed_by_file[item.rel_path] = parsed

                for sym in parsed.symbols:
                    sym_node = f"sym:{item.rel_path}:{sym.name}:{sym.start_line}"
                    self.graph.add_node(
                        sym_node,
                        node_type="symbol",
                        file_path=item.rel_path,
                        symbol_name=sym.name,
                        symbol_kind=sym.kind,
                        start_line=sym.start_line,
                        end_line=sym.end_line,
                    )
                    self.graph.add_edge(file_node, sym_node, edge_type="DEFINES")
                    symbol_nodes_by_name.setdefault(sym.name, []).append(sym_node)

        for rel_path, parsed in parsed_by_file.items():
            src_file_node = f"file:{rel_path}"
            is_test = _is_test_file(rel_path)

            for imp in parsed.imports:
                imp_parts = imp.split(".")
                candidate_file = "/".join(imp_parts) + ".py"
                target_file_node = f"file:{candidate_file}"
                if self.graph.has_node(target_file_node):
                    self.graph.add_edge(src_file_node, target_file_node, edge_type="IMPORTS")

            for sym in parsed.symbols:
                src_sym_node = f"sym:{rel_path}:{sym.name}:{sym.start_line}"
                for callee in sym.calls:
                    for target_sym_node in symbol_nodes_by_name.get(callee, []):
                        if target_sym_node != src_sym_node:
                            self.graph.add_edge(
                                src_sym_node,
                                target_sym_node,
                                edge_type="CALLS",
                                inferred="static_name_match",
                            )
                            target_fp = self.graph.nodes[target_sym_node].get("file_path")
                            if is_test and target_fp:
                                self.graph.add_edge(
                                    src_file_node,
                                    f"file:{target_fp}",
                                    edge_type="TESTS",
                                )

        return self.graph
