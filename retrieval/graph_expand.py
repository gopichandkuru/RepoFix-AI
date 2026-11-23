from typing import Dict, List, Set
import networkx as nx

from retrieval.bm25 import RetrievalCandidate


def expand_candidates_with_graph(
    graph: nx.DiGraph,
    seed_candidates: List[RetrievalCandidate],
    max_neighbors: int = 5,
    neighbor_decay: float = 0.5,
) -> List[RetrievalCandidate]:
    """Expand BM25 seed candidates over IMPORTS, CALLS, DEFINES, and TESTS edges."""
    if graph.number_of_nodes() == 0 or not seed_candidates:
        return list(seed_candidates)

    merged: Dict[str, RetrievalCandidate] = {}
    seed_file_scores: Dict[str, float] = {}

    for cand in seed_candidates:
        key = f"{cand.file_path}:{cand.symbol_name or '*'}"
        if key not in merged or cand.score > merged[key].score:
            merged[key] = cand
        seed_file_scores[cand.file_path] = max(seed_file_scores.get(cand.file_path, 0.0), cand.score)

    visited_files: Set[str] = set(seed_file_scores.keys())
    added_neighbors = 0

    for seed_fp, base_score in list(seed_file_scores.items()):
        seed_file_node = f"file:{seed_fp}"
        related_nodes: List[str] = []

        if graph.has_node(seed_file_node):
            related_nodes.extend(graph.successors(seed_file_node))
            related_nodes.extend(graph.predecessors(seed_file_node))

            for _, child, edata in graph.out_edges(seed_file_node, data=True):
                if edata.get("edge_type") == "DEFINES" and graph.has_node(child):
                    related_nodes.extend(graph.successors(child))
                    related_nodes.extend(graph.predecessors(child))

        for node_id in related_nodes:
            attrs = graph.nodes.get(node_id, {})
            n_fp = attrs.get("file_path")
            if not n_fp or n_fp in visited_files:
                continue

            visited_files.add(n_fp)
            added_neighbors += 1
            neighbor_score = round(base_score * neighbor_decay, 4)
            n_sym = attrs.get("symbol_name")
            key = f"{n_fp}:{n_sym or '*'}"

            if key not in merged:
                merged[key] = RetrievalCandidate(
                    file_path=n_fp,
                    symbol_name=n_sym,
                    symbol_kind=attrs.get("symbol_kind") or "file",
                    start_line=attrs.get("start_line"),
                    end_line=attrs.get("end_line"),
                    score=neighbor_score,
                    exact_symbol_hit=False,
                )

            if added_neighbors >= max_neighbors:
                break
        if added_neighbors >= max_neighbors:
            break

    return sorted(merged.values(), key=lambda c: c.score, reverse=True)
