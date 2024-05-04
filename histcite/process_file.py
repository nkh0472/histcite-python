from typing import Literal, Optional

import pandas as pd

from .parse_reference import parse_ref


class BuildRef:
    def __init__(self, docs_df: pd.DataFrame, source: Literal["wos", "cssci", "scopus"]):
        self.docs_df = docs_df
        self.source = source

    def iterator(self):
        for idx, cell in self.docs_df["CR"].items():
            if isinstance(cell, str):
                refs = cell.strip("; ").split("; ")
                for ref in refs:
                    parsed_ref = parse_ref(ref, self.source)  # type: ignore
                    if parsed_ref:
                        parsed_ref["node"] = idx  # type: ignore
                        yield parsed_ref

    def build(self):
        refs_df = pd.DataFrame(self.iterator())
        refs_df.drop_duplicates(ignore_index=True, inplace=True)
        if self.source == "scopus":
            refs_df["FAU"] = refs_df["FAU"].str.split(", ", n=1).str.get(0)
            refs_df["BP"] = refs_df["BP"].str.split("-").str.get(0)
        return refs_df


class IdentifyCitation:
    def __init__(self, docs_df: pd.DataFrame, refs_df: pd.DataFrame):
        self.docs_df = docs_df
        self.refs_df = refs_df

    def identify_citation_factory(
        self,
        compare_cols: list[str],
    ) -> pd.Series:
        use_cols = ["node"] + compare_cols
        docs_df = self.docs_df[use_cols]
        refs_df = self.refs_df[use_cols]

        # Drop rows with missing values
        if "DI" in compare_cols:
            thresh = 1
        else:
            thresh = len(compare_cols) - 1
        docs_df = docs_df.dropna(subset=compare_cols, thresh=thresh)
        refs_df = refs_df.dropna(subset=compare_cols, thresh=thresh)

        # Type convert
        col_type_mapper = {col: "string[pyarrow]" for col in compare_cols}
        docs_df = docs_df.astype(col_type_mapper)
        refs_df = refs_df.astype(col_type_mapper)

        # Lower case convert
        col_lower_case = [i for i in compare_cols if i != "PY"]
        for col in col_lower_case:
            docs_df[col] = docs_df[col].str.lower()
            refs_df[col] = refs_df[col].str.lower()

        shared_df = pd.merge(refs_df, docs_df, how="left", on=compare_cols, suffixes=("_x", "_y")).dropna(subset="node_y")
        cited_refs_series = shared_df.groupby("node_x")["node_y"].apply(list)
        return cited_refs_series

    def identify_wos_citation(self):
        def merge_list(a: Optional[list[int]], b: Optional[list[int]]) -> Optional[list[int]]:
            """Merge match results from doi and compare cols."""
            c = []
            if isinstance(a, list):
                c.extend(a)
            if isinstance(b, list):
                c.extend(b)
            if c:
                return list(set(c))

        # Fill NA value in VL field
        # Reference paper's VL info may contain in SO field.
        self.docs_df = self.docs_df.combine_first(self.docs_df["SO"].str.extract(r", VOLS? (?P<VL>[\d-]+)"))

        # DOI exists
        compare_cols = ["DI"]
        result_from_doi = self.identify_citation_factory(compare_cols)

        # DOI not exists
        compare_cols = ["FAU", "VL", "BP", "PY"]
        result_from_fields = self.identify_citation_factory(compare_cols)
        cited_refs_series = result_from_doi.combine(result_from_fields, merge_list)
        return cited_refs_series

    def identify_scopus_citation(self):
        compare_cols = ["FAU", "VL", "BP", "PY"]
        return self.identify_citation_factory(compare_cols)

    def identify_cssci_citation(self):
        compare_cols = ["FAU", "TI", "PY"]
        return self.identify_citation_factory(compare_cols)


class BuildCitation:
    def __init__(self, docs_df: pd.DataFrame, refs_df: pd.DataFrame, source: Literal["wos", "cssci", "scopus"]):
        self.docs_df = docs_df
        self.refs_df = refs_df
        self.source = source

    def build(self) -> pd.DataFrame:
        def reference2citation(cited_nodes_series: pd.Series) -> pd.Series:
            citing_nodes_series = pd.Series([[] for _ in range(cited_nodes_series.size)])
            for node, ref_list in cited_nodes_series.items():
                if len(ref_list) > 0:
                    for i in ref_list:
                        citing_nodes_series[i].append(node)
            return citing_nodes_series

        def list_to_str(list_like: Optional[list[int]]) -> Optional[str]:
            if list_like:
                return "; ".join([str(i) for i in list_like])

        if self.source == "wos":
            cited_nodes_series = IdentifyCitation(self.docs_df, self.refs_df).identify_wos_citation()

        elif self.source == "scopus":
            cited_nodes_series = IdentifyCitation(self.docs_df, self.refs_df).identify_scopus_citation()

        elif self.source == "cssci":
            cited_nodes_series = IdentifyCitation(self.docs_df, self.refs_df).identify_cssci_citation()

        # Remove self-citing of node
        for idx in cited_nodes_series.index:
            try:
                cited_nodes_series.loc[idx].remove(idx)
            except:
                pass
        cited_nodes_series = cited_nodes_series.reindex(self.docs_df["node"], fill_value=list())  # type: ignore
        citing_nodes_series = reference2citation(cited_nodes_series)

        lcr_field = cited_nodes_series.apply(len)
        lcs_field = citing_nodes_series.apply(len)
        citation_matrix = pd.DataFrame({"node": self.docs_df.node})
        citation_matrix["cited_nodes"] = cited_nodes_series.apply(list_to_str)
        citation_matrix["citing_nodes"] = citing_nodes_series.apply(list_to_str)
        citation_matrix["LCR"] = lcr_field
        citation_matrix["LCS"] = lcs_field
        return citation_matrix
