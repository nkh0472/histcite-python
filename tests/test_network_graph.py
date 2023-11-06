from pandas.core.frame import DataFrame
import pytest

from histcite.network_graph import GraphViz


def test_generate_dot_file(
    cssci_docs_df: DataFrame, cssci_citation_relation: DataFrame
):
    source = "cssci"
    graph = GraphViz(cssci_docs_df, cssci_citation_relation, source)
    graph_dot_file = graph.generate_dot_file(doc_id_object=10, edge_type="cited")
    assert graph_dot_file.startswith("digraph")

    graph_dot_file = graph.generate_dot_file(doc_id_object=10, edge_type="citing")
    assert graph_dot_file.startswith("digraph")

    graph_dot_file = graph.generate_dot_file(doc_id_object=10)
    assert graph_dot_file.startswith("digraph")

    doc_id_object = (
        cssci_citation_relation.sort_values("LCS", ascending=False).index[:10].tolist()
    )
    graph_dot_file = graph.generate_dot_file(doc_id_object)
    assert graph_dot_file.startswith("digraph")

    with pytest.raises(AssertionError) as exeinfo:
        graph.generate_dot_file(doc_id_object, edge_type="cited")
    assert (
        str(exeinfo.value)
        == "Argument <edge_type> should be None if <doc_id_object> contains >1 elements."
    )
