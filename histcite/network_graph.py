"""This module is used to generate network graph."""

from pathlib import Path
from typing import Literal, Optional, Union

import pandas as pd


class CitNetExplorer:
    """Generate publications.txt and citations.txt for CitNetExplorer sofaware."""

    def __init__(self, docs_df: pd.DataFrame, citation_matrix: pd.DataFrame):
        self.docs_df = docs_df
        self.citation_matrix = citation_matrix

    def generate_publications_df(self):
        use_cols = ["AU", "TI", "SO", "PY"]
        df = self.docs_df.loc[:, use_cols]
        if "DI" in self.docs_df.columns.to_list():
            df["DI"] = self.docs_df["DI"]
        df["cit_score"] = self.citation_matrix["LCS"]
        column_mapping = {
            "AU": "authors",
            "TI": "title",
            "SO": "source",
            "PY": "year",
            "DI": "doi",
        }
        df.rename(columns=column_mapping, inplace=True)
        return df

    def generate_citations_df(self):
        records = []
        for node in self.citation_matrix["node"]:
            cited_nodes = self.citation_matrix.loc[node, "cited_nodes"]
            if isinstance(cited_nodes, str):
                if "; " not in cited_nodes:
                    records.append((node, int(cited_nodes)))
                else:
                    records.extend((node, int(i)) for i in cited_nodes.split("; "))
        df = pd.DataFrame(records, columns=["citing_pub_index", "cited_pub_index"])
        # CitNetExplorer record index starts with 1
        return df + 1

    def export(self, folder_path: Path):
        Path.mkdir(folder_path, exist_ok=True)
        self.generate_citations_df().to_csv(folder_path / "citations.txt", sep="\t", index=False)
        self.generate_publications_df().to_csv(folder_path / "publications.txt", sep="\t", index=False)


class GraphViz:
    """Generate dot file for Graphviz. Support citation network of multi nodes and specific node."""

    def __init__(
        self,
        docs_df: pd.DataFrame,
        citation_matrix: pd.DataFrame,
    ):
        self.merged_docs_df = docs_df.merge(citation_matrix, on="node").dropna(subset="PY")

    def generate_edge(
        self,
        node: int,
        edge_type: Literal["cited", "citing"],
    ) -> Optional[list[tuple[int, int]]]:
        if edge_type == "cited":
            cell = self.merged_docs_df.loc[node, "cited_nodes"]
        elif edge_type == "citing":
            cell = self.merged_docs_df.loc[node, "citing_nodes"]

        if isinstance(cell, str):
            linked_nodes = [int(i) for i in cell.split("; ")]
            if edge_type == "cited":
                return [(node, ref) for ref in linked_nodes]
            elif edge_type == "citing":
                return [(citation, node) for citation in linked_nodes]

    def from_specific_node(
        self,
        node: int,
        edge_type: Literal["cited", "citing", None],
    ):
        if edge_type:
            total_edges = []
            node_records = {node}
            pending_nodes = [node]
            while pending_nodes:
                current_node = pending_nodes.pop()
                edges = self.generate_edge(current_node, edge_type)
                if edges:
                    total_edges.extend(edges)
                    if edge_type == "cited":
                        nodes = [i[1] for i in edges]
                    else:
                        nodes = [i[0] for i in edges]
                    adding_nodes = [i for i in nodes if i not in node_records]
                    pending_nodes.extend(adding_nodes)
                    node_records.update(adding_nodes)
            return total_edges
        else:
            return self.from_specific_node(node, "cited") + self.from_specific_node(node, "citing")

    def from_multi_node(self, node_list: list[int]) -> list[tuple[int, int]]:
        total_edges = []
        for node in node_list:
            edges = self.generate_edge(node, "cited")
            if edges:
                total_edges.extend(edges)
        total_edges = [(edge[0], edge[1]) for edge in total_edges if edge[1] in node_list]
        return total_edges

    def obtain_network_nodes(self, edge_list: list[tuple[int, int]]):
        source_nodes = [i[0] for i in edge_list]
        target_nodes = [i[1] for i in edge_list]
        total_nodes = sorted(set(source_nodes + target_nodes))
        return total_nodes, source_nodes

    def edges_to_dict(self, edge_list: list[tuple[int, int]], source_nodes: list[int]) -> dict[int, list[int]]:
        edge_dict = {node: [] for node in sorted(source_nodes)}
        for edge in edge_list:
            edge_dict[edge[0]].append(edge[1])
        return {k: sorted(v) for k, v in edge_dict.items()}

    @staticmethod
    def group_by_year(year_series: pd.Series, show_timeline: bool):
        """Obtain groups of node by year."""
        year_groups = year_series.groupby(year_series).groups
        year_list = list(year_groups.keys())
        node_groups = [list(i) for i in year_groups.values()]
        if show_timeline is True:
            for idx, year in enumerate(year_list):
                node_groups[idx].insert(0, year)
        return year_list, node_groups

    def generate_dot_file(
        self,
        node_obj: Union[list[int], int],
        edge_type: Literal["cited", "citing", None] = None,
        show_timeline: bool = True,
    ) -> str:
        if isinstance(node_obj, list) and len(node_obj) > 1:
            assert edge_type is None
            edge_list = self.from_multi_node(node_obj)
        elif isinstance(node_obj, int):
            edge_list = self.from_specific_node(node_obj, edge_type)

        total_nodes, source_nodes = self.obtain_network_nodes(edge_list)
        self.total_nodes = total_nodes

        year_series = self.merged_docs_df.loc[total_nodes, "PY"]
        year_list, node_groups = self.group_by_year(year_series, show_timeline)
        dot_groups = [f'\t{{rank=same; {" ".join([str(i) for i in group_index])}}};\n' for group_index in node_groups]

        edge_dict = self.edges_to_dict(edge_list, source_nodes)
        dot_edge_list = [f"\t{source} -> " + "{ " + " ".join([str(i) for i in edge_dict[source]]) + " };\n" for source in edge_dict.keys()]

        if show_timeline is True:
            sorted_year_list = year_list[::-1]
            year_edge_list = [
                (year, sorted_year_list[idx + 1]) for idx, year in enumerate(sorted_year_list) if idx < len(sorted_year_list) - 1
            ]
            dot_year_node_list = [f'\t{year} [ shape="plaintext" ];\n' for year in year_list]
            dot_year_edge_list = [f"\t{edge[0]} -> {edge[1]} [ style = invis ];\n" for edge in year_edge_list]
        else:
            dot_year_node_list, dot_year_edge_list = [], []

        dot_text = "digraph metadata{\n\trankdir = BT;\n"
        for dot_group in dot_groups:
            dot_text += dot_group

        for dot_year_node in dot_year_node_list:
            dot_text += dot_year_node

        for dot_year_edge in dot_year_edge_list:
            dot_text += dot_year_edge

        for dot_edge in dot_edge_list:
            dot_text += dot_edge
        dot_text += "}"
        return dot_text

    def generate_graph_node_info(self) -> pd.DataFrame:
        """Generate dataframe of graph node info. Columns differ according to `source`."""
        use_cols = ["node", "AU", "TI", "PY", "SO", "LCS"]
        graph_node_info = self.merged_docs_df.loc[self.total_nodes, use_cols]
        if "TC" in self.merged_docs_df.columns.to_list():
            graph_node_info["GCS"] = self.merged_docs_df["TC"]
        return graph_node_info

    def export_graph_node_info(self, folder_path: Path):
        self.generate_graph_node_info().to_excel(folder_path / "graph_node_info.xlsx", index=False)
