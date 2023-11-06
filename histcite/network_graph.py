"""This module is used to generate network graph in dot language."""
from pathlib import Path
from typing import Hashable, Literal, Optional, Union

import pandas as pd


class GraphViz:
    """Generate dot file for Graphviz. Support citation network of multi docs and specific doc."""

    def __init__(
        self,
        docs_df: pd.DataFrame,
        citation_relation: pd.DataFrame,
        source: Literal["wos", "cssci", "scopus"],
    ):
        """
        Args:
            docs_df: DataFrame of docs.
            citation_relation: DataFrame of citation relationship.
            source: Data source. `wos`, `cssci` or `scopus`.
        """
        self._empty_year_index: pd.Index = docs_df[docs_df["PY"].isna()].index
        self._merged_docs_df: pd.DataFrame = docs_df.merge(
            citation_relation,
            left_index=True,
            right_index=True,
            suffixes=(None, "_y"),
        ).drop(columns=["doc_id_y"])
        self._source: Literal["wos", "cssci", "scopus"] = source

    @classmethod
    def _generate_edge(
        cls,
        doc_id: int,
        related_doc_id_list: Union[str, list[int]],
        edge_type: Literal["cited", "citing"],
    ) -> set[tuple[int, int]]:
        if isinstance(related_doc_id_list, str):
            related_doc_id_list = [int(i) for i in related_doc_id_list.split(";")]

        if edge_type == "cited":
            return {(doc_id, ref) for ref in related_doc_id_list}
        elif edge_type == "citing":
            return {(citation, doc_id) for citation in related_doc_id_list}

    def _generate_edge_set_from_specific_doc(
        self,
        doc_id: int,
        edge_type: Literal["cited", "citing"],
    ) -> set[tuple[int, int]]:
        def pipeline(doc_id: int):
            if edge_type == "cited":
                cell = self._merged_docs_df.at[doc_id, "cited_doc_id"]
            elif edge_type == "citing":
                cell = self._merged_docs_df.at[doc_id, "citing_doc_id"]

            if isinstance(cell, str):
                related_doc_id = [int(i) for i in cell.split(";")]
                if related_doc_id is not None:
                    pending_doc_id.extend(related_doc_id)
                    edge_set.update(
                        self._generate_edge(doc_id, related_doc_id, edge_type)
                    )

        edge_set: set[tuple[int, int]] = set()
        pending_doc_id: list[int] = []
        pipeline(doc_id)
        while pending_doc_id:
            current_doc_id = pending_doc_id.pop()
            pipeline(current_doc_id)
        return edge_set

    def _generate_edge_set_from_multi_doc(
        self, doc_id_list: list[int]
    ) -> set[tuple[int, int]]:
        edge_set: set[tuple[int, int]] = set()
        for idx in doc_id_list:
            cited_doc_id = self._merged_docs_df.loc[idx, "cited_doc_id"]
            citing_doc_id = self._merged_docs_df.loc[idx, "citing_doc_id"]
            if isinstance(cited_doc_id, str):
                edge_set.update(self._generate_edge(idx, cited_doc_id, "cited"))
            if isinstance(citing_doc_id, str):
                edge_set.update(self._generate_edge(idx, citing_doc_id, "citing"))
        edge_set = {
            (edge[0], edge[1])
            for edge in edge_set
            if edge[0] in doc_id_list and edge[1] in doc_id_list
        }
        return edge_set

    def _generate_edge_set(self) -> dict[int, list[int]]:
        if len(self.doc_id_object) > 1:
            edge_set = self._generate_edge_set_from_multi_doc(self.doc_id_object)
        else:
            initial_doc_id = self.doc_id_object[0]

            if self.edge_type == "cited":
                edge_set = self._generate_edge_set_from_specific_doc(
                    initial_doc_id, "cited"
                )
            elif self.edge_type == "citing":
                edge_set = self._generate_edge_set_from_specific_doc(
                    initial_doc_id, "citing"
                )
            elif self.edge_type is None:
                edge_set = self._generate_edge_set_from_specific_doc(
                    initial_doc_id, "cited"
                )
                edge_set.update(
                    self._generate_edge_set_from_specific_doc(initial_doc_id, "citing")
                )
            else:
                raise ValueError(
                    'Argument <edge_type> must be one of "cited", "citing" or None'
                )

        # Drop node without PY info
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
        """Obtain groups of doc_id by year."""
        year_series = self._merged_docs_df.loc[self.node_list, "PY"]
        year_groups = year_series.groupby(year_series).groups.items()
        year_list = [i[0] for i in year_groups]
        grouped_doc_id = [list(i[1]) for i in year_groups]
        if self.show_timeline is True:
            for idx, year in enumerate(year_list):
                grouped_doc_id[idx].insert(0, year)
        return grouped_doc_id, year_list

    def generate_dot_file(
        self,
        doc_id_object: Union[list[int], int],
        edge_type: Optional[Literal["cited", "citing"]] = None,
        show_timeline: bool = True,
    ) -> str:
        """
        Args:
            doc_id_object: Specific doc_id or list of doc_id. If list, only show edges between these doc_id.
            edge_type: Only for specific doc_id. It can be `cited`, `citing` or `None`. If `None`, show both `cited` and `citing` edges. Default None.
            show_timeline: Whether show timeline. In some cases, timeline may be disorderly, so you can set it to `False`. Default True.

        Returns:
            Dot file content.
        """
        if isinstance(doc_id_object, list) and len(doc_id_object) > 1:
            assert (
                edge_type is None
            ), "Argument <edge_type> should be None if <doc_id_object> contains >1 elements."
            self.doc_id_object = doc_id_object
        elif isinstance(doc_id_object, int):
            assert (
                doc_id_object in self._merged_docs_df.index
            ), "Don't specify <doc_id> not in <docs_df>."
            assert (
                doc_id_object not in self._empty_year_index
            ), "Don't specify <doc_id> without <PY> info."
            self.doc_id_object = [doc_id_object]
        self.edge_type = edge_type
        self.show_timeline = show_timeline

        edge_dict = self._generate_edge_set()
        grouped_doc_id, year_list = self._obtain_groups()

        dot_groups = [
            f'\t{{rank=same; {" ".join([str(i) for i in group_index])}}};\n'
            for group_index in grouped_doc_id
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
            use_cols = ["doc_id", "AU", "TI", "PY", "SO", "LCS", "TC"]
        elif self._source == "cssci":
            use_cols = ["doc_id", "AU", "TI", "PY", "SO", "LCS"]
        elif self._source == "scopus":
            use_cols = ["doc_id", "AU", "TI", "PY", "SO", "LCS", "TC"]
        else:
            raise ValueError("invalid source type")
        graph_node_info = self._merged_docs_df.loc[self.node_list, use_cols]
        if "TC" in graph_node_info.columns:
            graph_node_info.rename(columns={"TC": "GCS"}, inplace=True)
        return graph_node_info

    def _export_graph_node_info(self, file_path: Path):
        self.generate_graph_node_info().to_excel(file_path, index=False)
