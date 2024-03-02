from typing import Literal

import pandas as pd

from .parse_reference import ParseReference
from .recognize_reference import RecognizeReference


class ProcessFile:
    """Process docs file, extract references and citation relationship."""

    def __init__(self, docs_df: pd.DataFrame, source: Literal["wos", "cssci", "scopus"]):
        """
        Args:
            docs_df: DataFrame of docs.
            source: Data source. `wos`, `cssci` or `scopus`.
        """
        self.docs_df: pd.DataFrame = docs_df
        self.source: Literal["wos", "cssci", "scopus"] = source

    @staticmethod
    def concat_refs(
        cr_field: pd.Series,
        source: Literal["wos", "cssci", "scopus"],
    ) -> pd.DataFrame:
        """Concat all parsed references and return dataframe.

        Args:
            cr_field: The CR field of docs_df.
            source: Data source. 'wos', 'cssci' or 'scopus'.

        Returns:
            DataFrame of references.
        """

        def parsed_ref_iterator():
            for idx, cell in cr_field.items():
                if isinstance(cell, str):
                    parsed_refs = ParseReference().parse_ref_cell(cell, source, idx)  # type: ignore
                    if parsed_refs is not None:
                        for parsed_ref in parsed_refs:
                            yield parsed_ref

        return pd.DataFrame(parsed_ref_iterator())

    def extract_reference(self) -> pd.DataFrame:
        """Extract total references and return reference dataframe."""

        def assign_ref_id(refs_df: pd.DataFrame) -> pd.Series:
            if self.source == "wos":
                check_cols = ["FAU", "PY", "J9", "BP"]
            elif self.source == "cssci":
                check_cols = ["FAU", "TI"]
            elif self.source == "scopus":
                check_cols = ["FAU", "TI"]
            else:
                raise ValueError("Invalid source type")
            return refs_df.groupby(by=check_cols, sort=False, dropna=False).ngroup()

        cr_field = self.docs_df["CR"]
        if self.source == "wos":
            refs_df = self.concat_refs(cr_field, "wos")
        elif self.source == "cssci":
            refs_df = self.concat_refs(cr_field, "cssci")
        elif self.source == "scopus":
            refs_df = self.concat_refs(cr_field, "scopus")
        else:
            raise ValueError("Invalid source type")

        # Maybe duplicate reference in some docs' references
        refs_df.drop_duplicates(ignore_index=True, inplace=True)
        refs_df.insert(0, "ref_index", refs_df.index)
        refs_df.insert(1, "ref_id", assign_ref_id(refs_df))
        refs_df = refs_df.convert_dtypes(dtype_backend="pyarrow")
        return refs_df

    def process_citation(self, refs_df: pd.DataFrame) -> pd.DataFrame:
        """Return citation relationship dataframe."""

        def reference2citation(cited_doc_id_series: pd.Series) -> pd.Series:
            citing_doc_id_series = pd.Series([[] for i in range(len(cited_doc_id_series))])
            for doc_id, ref_list in cited_doc_id_series.items():
                if len(ref_list) > 0:
                    for ref_index in ref_list:
                        citing_doc_id_series[ref_index].append(doc_id)
            return citing_doc_id_series

        def remove_duplicate_id(a: list, b: int):
            return [i for i in a if i != b]

        if self.source == "wos":
            cited_doc_id_series = RecognizeReference.recognize_wos_reference(self.docs_df, refs_df)

        elif self.source == "cssci":
            cited_doc_id_series = RecognizeReference.recognize_cssci_reference(self.docs_df, refs_df)

        elif self.source == "scopus":
            cited_doc_id_series = RecognizeReference.recognize_scopus_reference(self.docs_df, refs_df)

        else:
            raise ValueError("Invalid source type")

        cited_doc_id_series = cited_doc_id_series.reindex(self.docs_df["doc_id"])
        cited_doc_id_series = cited_doc_id_series.apply(lambda x: x if isinstance(x, list) else [])
        cited_doc_id_series = cited_doc_id_series.to_frame().apply(
            lambda x: remove_duplicate_id(x["doc_id_y"], x.name), axis=1
        )
        citing_doc_id_series = reference2citation(cited_doc_id_series)

        lcr_field = cited_doc_id_series.apply(len)
        lcs_field = citing_doc_id_series.apply(len)
        citation_relation = pd.DataFrame({"doc_id": self.docs_df.doc_id})
        citation_relation["cited_doc_id"] = ["; ".join([str(j) for j in i]) if i else None for i in cited_doc_id_series]
        citation_relation["citing_doc_id"] = [
            "; ".join([str(j) for j in i]) if i else None for i in citing_doc_id_series
        ]
        citation_relation["LCR"] = lcr_field
        citation_relation["LCS"] = lcs_field
        return citation_relation
