"""This module used to recognize local references of a doc."""

from typing import Optional

import pandas as pd


class RecognizeReference:
    @staticmethod
    def recognize_refs_factory(
        docs_df: pd.DataFrame,
        refs_df: pd.DataFrame,
        compare_cols: list[str],
        drop_duplicates: bool = False,
    ) -> pd.Series:
        """
        A factory function to recognize local references of doc records.

        Args:
            docs_df: DataFrame of docs.
            refs_df: DataFrame of references.
            compare_cols: Columns to compare. e.g. `["FAU", "TI"]`.
            drop_duplicates: Whether to drop duplicated rows with same values in `compare_cols`. Default False.

        Returns:
            A Series of lists, each list contains the indexes of local references.
        """
        # Drop rows with missing values
        docs_df = docs_df.dropna(subset=compare_cols)
        refs_df = refs_df.dropna(subset=compare_cols)

        if drop_duplicates is True:
            docs_df = docs_df.drop_duplicates(subset=compare_cols)

        # Type convert
        lower_case_cols = [col for col in compare_cols if docs_df[col].dtype != "string[pyarrow]"]
        if lower_case_cols:
            docs_df = docs_df.astype({col: "string[pyarrow]" for col in lower_case_cols})

        # Lower case convert
        for col in compare_cols:
            if col not in ["PY"]:
                docs_df.loc[:, col] = docs_df[col].str.lower()
                refs_df.loc[:, col] = refs_df[col].str.lower()

        child_docs_df = docs_df[["doc_id"] + compare_cols]
        child_refs_df = refs_df[["doc_id", "ref_index"] + compare_cols]
        shared_df = pd.merge(child_refs_df, child_docs_df, how="left", on=compare_cols, suffixes=("_x", "_y")).dropna(
            subset="doc_id_y"
        )
        cited_refs_series = shared_df.groupby("doc_id_x")["doc_id_y"].apply(list)
        return cited_refs_series

    @staticmethod
    def recognize_wos_reference(docs_df: pd.DataFrame, refs_df: pd.DataFrame) -> pd.Series:
        """Recognize local references of docs from Web of Science.

        If `DOI` exists, use `DOI` to recognize references.
        Otherwise, use `FAU`, `PY`, `J9`, `BP` to recognize references.

        Args:
            docs_df: DataFrame of docs.
            refs_df: DataFrame of references.

        Returns:
            A Series of lists, each list contains the indexes of local references.
        """

        def merge_list(a: Optional[list[int]], b: Optional[list[int]]) -> Optional[list[int]]:
            c = set()
            if isinstance(a, list):
                c.update(a)
            if isinstance(b, list):
                c.update(b)
            if c:
                return list(c)

        # DOI exists
        compare_cols = ["DI"]
        result_from_doi = RecognizeReference.recognize_refs_factory(
            docs_df[docs_df["DI"].notna()], refs_df[refs_df["DI"].notna()], compare_cols
        )

        # DOI not exists
        compare_cols = ["FAU", "PY", "J9", "BP"]
        result_from_fields = RecognizeReference.recognize_refs_factory(docs_df, refs_df, compare_cols)
        cited_refs_series = result_from_doi.combine(result_from_fields, merge_list)
        return cited_refs_series

    @staticmethod
    def recognize_cssci_reference(docs_df: pd.DataFrame, refs_df: pd.DataFrame) -> pd.Series:
        """Recognize local references of docs from CSSCI.

        Use `FAU`, `TI` to recognize references.

        Args:
            docs_df: DataFrame of docs.
            refs_df: DataFrame of references.

        Returns:
            A Series of lists, each list contains the indexes of local references.
        """
        compare_cols = ["FAU", "TI"]
        return RecognizeReference.recognize_refs_factory(docs_df, refs_df, compare_cols)

    @staticmethod
    def recognize_scopus_reference(docs_df: pd.DataFrame, refs_df: pd.DataFrame) -> pd.Series:
        """Recognize local references of docs from Scopus.

        Use `FAU`, `TI` to recognize references.

        Args:
            docs_df: DataFrame of docs.
            refs_df: DataFrame of references.

        Returns:
            A Series of lists, each list contains the indexes of local references.
        """
        compare_cols = ["FAU", "TI"]
        return RecognizeReference.recognize_refs_factory(docs_df, refs_df, compare_cols, drop_duplicates=True)
