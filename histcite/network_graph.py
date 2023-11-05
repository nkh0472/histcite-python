"""This module is used to generate network graph in dot language."""
from pathlib import Path
from typing import Hashable, Literal, Optional, Union

import pandas as pd


class GraphViz:
    """Generate dot file for Graphviz. Support citation network of multi docs and specific doc."""

    def __init__(
        self,
        docs_df: pd.DataFrame,
        citation_relationship: pd.DataFrame,
        source: Literal["wos", "cssci", "scopus"],
    ):
        """
        Args:
            docs_df: DataFrame of docs.
            citation_relationship: DataFrame of citation relationship.
            source: Data source. `wos`, `cssci` or `scopus`.
        """
        self._empty_year_index: pd.Index = docs_df[docs_df["PY"].isna()].index
        self._merged_docs_df: pd.DataFrame = docs_df.merge(
            citation_relationship,
            left_index=True,
            right_index=True,
            suffixes=(None, "_y"),
        ).drop(columns=["doc_index_y"])
        self._source: Literal["wos", "cssci", "scopus"] = source

    @staticmethod
    def _generate_edge(
        doc_index: int,
        related_doc_index_list: Union[str, list[int]],
        citation_type: Literal["cited", "citing"],
    ) -> set[tuple[int, int]]:
        if isinstance(related_doc_index_list, str):
            related_doc_index_list = [int(i) for i in related_doc_index_list.split(";")]
        if citation_type == "cited":
            return {(doc_index, ref) for ref in related_doc_index_list}
        else:
            return {(citation, doc_index) for citation in related_doc_index_list}

    def _generate_edge_set_from_specific_doc(
        self,
        doc_index: int,
        edge_type: Literal["cited", "citing"],
    ) -> set[tuple[int, int]]:
        def pipeline(doc_index: int):
            if edge_type == "cited":
                cell = self._merged_docs_df.loc[doc_index, "cited_doc_index"]
            else:
                cell = self._merged_docs_df.loc[doc_index, "citing_doc_index"]
            if isinstance(cell, str):
                related_doc_index = [int(i) for i in cell.split(";")]
                pending_doc_index.extend(related_doc_index)
                if edge_type == "cited":
                    edge_set.update(
                        self._generate_edge(doc_index, related_doc_index, "cited")
                    )
                else:
                    edge_set.update(
                        self._generate_edge(doc_index, related_doc_index, "citing")
                    )

        edge_set: set[tuple[int, int]] = set()
        pending_doc_index: list[int] = []
        pipeline(doc_index)
        while pending_doc_index:
            current_doc_index = pending_doc_index.pop()
            pipeline(current_doc_index)
        return edge_set

    def _generate_edge_set_from_multi_doc(
        self, doc_indices: list[int]
    ) -> set[tuple[int, int]]:
        edge_set: set[tuple[int, int]] = set()
        for idx in doc_indices:
            cited_doc_index = self._merged_docs_df.loc[idx, "cited_doc_index"]
            citing_doc_index = self._merged_docs_df.loc[idx, "citing_doc_index"]
            if isinstance(cited_doc_index, str):
                edge_set.update(self._generate_edge(idx, cited_doc_index, "cited"))
            if isinstance(citing_doc_index, str):
                edge_set.update(self._generate_edge(idx, citing_doc_index, "citing"))
        edge_set = {
            (edge[0], edge[1])
            for edge in edge_set
            if edge[0] in doc_indices and edge[1] in doc_indices
        }
        return edge_set

    def _generate_edge_set(self) -> dict[int, list[int]]:
        if len(self.doc_indices) > 1:
            edge_set = self._generate_edge_set_from_multi_doc(self.doc_indices)
        else:
            initial_doc_index = self.doc_indices[0]
            if self.edge_type == "cited":
                edge_set = self._generate_edge_set_from_specific_doc(
                    initial_doc_index, "cited"
                )
            elif self.edge_type == "citing":
                edge_set = self._generate_edge_set_from_specific_doc(
                    initial_doc_index, "citing"
                )
            elif self.edge_type is None:
                edge_set = self._generate_edge_set_from_specific_doc(
                    initial_doc_index, "cited"
                )
                edge_set.update(
                    self._generate_edge_set_from_specific_doc(
                        initial_doc_index, "citing"
                    )
                )
            else:
                raise ValueError(
                    'Argument <edge_type> must be one of "cited", "citing" or None'
                )

        # Drop nodes without PY info
        if len(self._empty_year_index) > 0 and self.show_timeline is True:
            edge_set = {
                (edge[0], edge[1])
                for edge in edge_set
                if edge[0] not in self._empty_year_index
                and edge[1] not in self._empty_year_index
            }

        # Build node_list according to edges
        source_node = set([i for i, _ in edge_set])
        target_node = set([j for _, j in edge_set])
        node_list = sorted(source_node | target_node)
        self.node_list = node_list

        edge_dict: dict[int, list[int]] = {i: [] for i in sorted(source_node)}
        for edge in edge_set:
            edge_dict[edge[0]].append(edge[1])
        return edge_dict

    def _obtain_groups(self) -> tuple[list[list[Hashable]], list[Hashable]]:
        """Obtain groups of doc_index by year."""
        year_series = self._merged_docs_df.loc[self.node_list, "PY"]
        year_groups = year_series.groupby(year_series).groups.items()
        year_list = [i[0] for i in year_groups]
        grouped_doc_index = [list(i[1]) for i in year_groups]
        if self.show_timeline is True:
            for idx, year in enumerate(year_list):
                grouped_doc_index[idx].insert(0, year)
        return grouped_doc_index, year_list

    def generate_dot_file(
        self,
        doc_indices: Union[list[int], int],
        edge_type: Optional[Literal["cited", "citing"]] = None,
        show_timeline: bool = True,
    ) -> str:
        """
        Args:
            doc_indices: Specific doc_index or list of doc_index. If list, only show edges between these doc_index.
            edge_type: Only for specific doc_index. It can be `cited`, `citing` or `None`. If `None`, show both `cited` and `citing` edges. Default None.
            show_timeline: Whether show timeline. In some cases, timeline may be disorderly, so you can set it to `False`. Default True.

        Returns:
            Dot file content.
        """
        if isinstance(doc_indices, list) and len(doc_indices) > 1:
            assert (
                edge_type is None
            ), "Argument <edge_type> should be None if <doc_indices> contains >1 elements."
            self.doc_indices = doc_indices
        elif isinstance(doc_indices, int):
            assert (
                doc_indices in self._merged_docs_df.index
            ), "Don't specify <doc_index> not in <docs_df>."
            assert (
                doc_indices not in self._empty_year_index
            ), "Don't specify <doc_index> without <PY> info."
            self.doc_indices = [doc_indices]
        self.edge_type = edge_type
        self.show_timeline = show_timeline

        edge_dict = self._generate_edge_set()
        grouped_doc_index, year_list = self._obtain_groups()

        dot_groups = [
            f'\t{{rank=same; {" ".join([str(i) for i in group_index])}}};\n'
            for group_index in grouped_doc_index
        ]
        dot_edge_list = [
            f"\t{source} -> "
            + "{ "
            + " ".join([str(i) for i in edge_dict[source]])
            + " };\n"
            for source in edge_dict.keys()
        ]

        if self.show_timeline is True:
            reversed_year_list = year_list[::-1]
            year_edge_list = [
                (year, reversed_year_list[idx + 1])
                for idx, year in enumerate(reversed_year_list)
                if idx < len(reversed_year_list) - 1
            ]
            dot_year_node_list = [
                f'\t{year} [ shape="plaintext" ];\n' for year in year_list
            ]
            dot_year_edge_list = [
                f"\t{edge[0]} -> {edge[1]} [ style = invis ];\n"
                for edge in year_edge_list
            ]
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
        """Generate dataframe of graph node info. Columns differ according to `source`.

        Returns:
            Dataframe of graph node info.
        """
        if self._source == "wos":
            use_cols = ["doc_index", "AU", "TI", "PY", "SO", "LCS", "TC"]
        elif self._source == "cssci":
            use_cols = ["doc_index", "AU", "TI", "PY", "SO", "LCS"]
        elif self._source == "scopus":
            use_cols = ["doc_index", "AU", "TI", "PY", "SO", "LCS", "TC"]
        else:
            raise ValueError("invalid source type")
        graph_node_info = self._merged_docs_df.loc[self.node_list, use_cols]
        if "TC" in graph_node_info.columns:
            graph_node_info.rename(columns={"TC": "GCS"}, inplace=True)
        return graph_node_info

    def _export_graph_node_info(self, file_path: Path):
        self.generate_graph_node_info().to_excel(file_path, index=False)
