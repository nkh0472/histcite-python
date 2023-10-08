import pytest
import pandas as pd
from histcite.network_graph import GraphViz


source_type = "cssci"
docs_df_path = "tests/testdata/docs_df.csv"
citation_relationship_path = "tests/testdata/citation_relationship.csv"

docs_df = pd.read_csv(docs_df_path, dtype_backend="pyarrow")
citation_relationship = pd.read_csv(citation_relationship_path, dtype_backend="pyarrow")
graph = GraphViz(docs_df, citation_relationship, source_type)


def test_generate_dot_file():
    graph_dot_file = graph.generate_dot_file(doc_indices=10, edge_type="cited")
    assert graph_dot_file.startswith("digraph")

    graph_dot_file = graph.generate_dot_file(doc_indices=10, edge_type="citing")
    assert graph_dot_file.startswith("digraph")

    graph_dot_file = graph.generate_dot_file(doc_indices=10)
    assert graph_dot_file.startswith("digraph")

    doc_indices = (
        citation_relationship.sort_values("LCS", ascending=False).index[:10].tolist()
    )
    graph_dot_file = graph.generate_dot_file(doc_indices)
    assert graph_dot_file.startswith("digraph")

    with pytest.raises(AssertionError) as exeinfo:
        graph.generate_dot_file(doc_indices, edge_type="cited")
    assert (
        str(exeinfo.value)
        == "Argument <edge_type> should be None if <doc_indices> contains >1 elements."
    )


def test_generate_graph_node_info():
    graph.generate_dot_file(doc_indices=10)
    graph_node_info = graph.generate_graph_node_info()
    assert isinstance(graph_node_info, pd.DataFrame)
    assert "GCS" not in graph_node_info.columns
