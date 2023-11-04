from pandas.core.frame import DataFrame
import pytest
from histcite.network_graph import GraphViz


def test_generate_dot_file(
    cssci_docs_df: DataFrame, cssci_citation_relationship: DataFrame
):
    source = "cssci"
    graph = GraphViz(cssci_docs_df, cssci_citation_relationship, source)
    graph_dot_file = graph.generate_dot_file(doc_indices=10, edge_type="cited")
    assert graph_dot_file.startswith("digraph")

    graph_dot_file = graph.generate_dot_file(doc_indices=10, edge_type="citing")
    assert graph_dot_file.startswith("digraph")

    graph_dot_file = graph.generate_dot_file(doc_indices=10)
    assert graph_dot_file.startswith("digraph")

    doc_indices = (
        cssci_citation_relationship.sort_values("LCS", ascending=False)
        .index[:10]
        .tolist()
    )
    graph_dot_file = graph.generate_dot_file(doc_indices)
    assert graph_dot_file.startswith("digraph")

    with pytest.raises(AssertionError) as exeinfo:
        graph.generate_dot_file(doc_indices, edge_type="cited")
    assert (
        str(exeinfo.value)
        == "Argument <edge_type> should be None if <doc_indices> contains >1 elements."
    )
