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
            try:
                docs_df = docs_df.drop_duplicates(subset=compare_cols)
            except Exception:
                pass

        docs_df = docs_df[["doc_id"] + compare_cols]
        refs_df = refs_df[["doc_id", "ref_index"] + compare_cols]
        shared_df = pd.merge(
            refs_df, docs_df, how="left", on=compare_cols, suffixes=("_x", "_y")
        ).dropna(subset="doc_id_y")
        shared_df = shared_df.astype({"doc_id_y": "int64"})
        cited_refs_series = shared_df.groupby("doc_id_x")["doc_id_y"].apply(list)
        cited_refs_series = cited_refs_series.apply(lambda x: sorted(x))
        # local_refs_series = shared_df["ref_index"].reset_index(drop=True)
        return cited_refs_series

    @staticmethod
    def recognize_wos_reference(
        docs_df: pd.DataFrame, refs_df: pd.DataFrame
    ) -> pd.Series:
        """Recognize local references of docs from Web of Science.

        If `DOI` exists, use `DOI` to recognize references.
        Otherwise, use `FAU`, `PY`, `J9`, `BP` to recognize references.

        Args:
            docs_df: DataFrame of docs.
            refs_df: DataFrame of references.

        Returns:
            A Series of lists, each list contains the indexes of local references.
        """

        def _merge_lists(
            list1: Optional[list[int]], list2: Optional[list[int]]
        ) -> Optional[list[int]]:
            if isinstance(list1, list) and isinstance(list2, list):
                return list1 + list2
            else:
                if isinstance(list1, list):
                    return list1
                elif isinstance(list2, list):
                    return list2
                else:
                    return None

        # DOI exists
        compare_cols_doi = ["DI"]
        result_doi = RecognizeReference.recognize_refs_factory(
            docs_df, refs_df, compare_cols_doi
        )

        # DOI not exists
        compare_cols = ["FAU", "PY", "J9", "BP"]
        result = RecognizeReference.recognize_refs_factory(
            docs_df[docs_df["DI"].isna()], refs_df[refs_df["DI"].isna()], compare_cols
        )
        cited_refs_series = result_doi.combine(result, _merge_lists)
        # local_refs_series = pd.concat([result_doi[1], result[1]])
        return cited_refs_series

    @staticmethod
    def recognize_cssci_reference(
        docs_df: pd.DataFrame, refs_df: pd.DataFrame
    ) -> pd.Series:
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
    def recognize_scopus_reference(
        docs_df: pd.DataFrame, refs_df: pd.DataFrame
    ) -> pd.Series:
        """Recognize local references of docs from Scopus.

        Use `FAU`, `TI` to recognize references.

        Args:
            docs_df: DataFrame of docs.
            refs_df: DataFrame of references.

        Returns:
            A Series of lists, each list contains the indexes of local references.
        """
        compare_cols = ["FAU", "TI"]
        return RecognizeReference.recognize_refs_factory(
            docs_df, refs_df, compare_cols, drop_duplicates=True
        )
