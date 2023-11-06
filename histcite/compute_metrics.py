"""This module is used to generate and export descriptive statistics.

Supported statistic units:
- Author
- Journal
- Keyword
- Institution
- Publication year
- Document type
"""
from pathlib import Path
from typing import Literal, Optional

import pandas as pd


class ComputeMetrics:
    """Compute descriptive statistics of docs."""

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
        self._merged_docs_df: pd.DataFrame = docs_df.merge(
            citation_relation[["doc_id", "LCR", "LCS"]], on="doc_id"
        )
        self._source: Literal["wos", "cssci", "scopus"] = source

    def generate_df_factory(
        self,
        use_cols: list[str],
        col: str,
        split_char: Optional[str] = None,
        str_lower: bool = False,
        sort_by_col: Literal["Recs", "TLCS", "TGCS"] = "Recs",
    ) -> pd.DataFrame:
        """A factory method to generate DataFrame of specific field.

        Args:
            use_cols: Columns to use. e.g. `["AU", "LCS", "TC"]`.
            col: Column to analyze. e.g. `AU`.
            split_char: Whether to split string. e.g. `; `. Default None.
            str_lower: Whether to convert string to lowercase. Default False.
            sort_by_col: Sort DataFrame by column. `Recs`, `TLCS` or `TGCS`. Default `Recs`.

        Returns:
            A DataFrame with some statitical metrics.
        """
        assert col in use_cols, "Argument <col> must be in use_cols"
        if sort_by_col == "TLCS":
            assert "LCS" in use_cols, "LCS must be in <use_cols> when sorting by TLCS"
        elif sort_by_col == "TGCS":
            assert "TC" in use_cols, "TC must be in <use_cols> when sorting by TGCS"

        df = self._merged_docs_df[use_cols]
        if split_char:
            df = df.dropna(subset=[col])
            df = df.astype({col: "str"})
            if str_lower:
                df[col] = df[col].str.lower()
            df[col] = df[col].str.split(split_char)
            df = df.explode(col)
            df = df.reset_index(drop=True)

        if "LCS" in use_cols:
            if "TC" in use_cols:
                grouped_df = df.groupby(col).agg(
                    {col: "count", "LCS": "sum", "TC": "sum"}
                )
            else:
                grouped_df = df.groupby(col).agg({col: "count", "LCS": "sum"})
        else:
            grouped_df = df.groupby(col).agg({col: "count"})

        grouped_df.rename(
            columns={col: "Recs", "LCS": "TLCS", "TC": "TGCS"}, inplace=True
        )
        # e.g. Andersson, Gerhard (7202645907)
        if col == "Author full names":
            grouped_df.index = grouped_df.index.str.replace(r" \(\d+\)", "", regex=True)

        if not sort_by_col:
            sort_by_col = "Recs"
        return grouped_df.sort_values(sort_by_col, ascending=False)

    def generate_record_df(self) -> pd.DataFrame:
        """Return record DataFrame."""
        if self._source in ["wos", "scopus"]:
            use_cols = [
                "AU",
                "TI",
                "SO",
                "PY",
                "TI",
                "LCS",
                "TC",
                "LCR",
                "NR",
                "source file",
            ]
        elif self._source == "cssci":
            use_cols = ["AU", "TI", "SO", "PY", "LCS", "LCR", "NR", "source file"]
        else:
            raise ValueError("Invalid source type")
        records_df = self._merged_docs_df[use_cols]
        if "TC" in use_cols:
            records_df = records_df.rename(columns={"TC": "GCS"})
        if "NR" in use_cols:
            records_df = records_df.rename(columns={"NR": "GCR"})
        return records_df

    def generate_author_df(self) -> pd.DataFrame:
        """Return author DataFrame."""
        if self._source == "wos":
            use_cols = ["AU", "LCS", "TC"]
        elif self._source == "cssci":
            use_cols = ["AU", "LCS"]
        elif self._source == "scopus":
            use_cols = ["Author full names", "LCS", "TC"]
        else:
            raise ValueError("Invalid source type")
        return self.generate_df_factory(use_cols, use_cols[0], "; ")

    def generate_keyword_df(self) -> pd.DataFrame:
        """Return keyword DataFrame."""
        if self._source in ["wos", "scopus"]:
            use_cols = ["DE", "LCS", "TC"]
        elif self._source == "cssci":
            use_cols = ["DE", "LCS"]
        else:
            raise ValueError("Invalid source type")
        return self.generate_df_factory(use_cols, "DE", "; ", True)

    def generate_institution_df(self) -> pd.DataFrame:
        """Return institution DataFrame. Not support Scopus."""
        assert (
            self._source != "scopus"
        ), "Scopus is not supported to analyze <institution> field yet."
        if self._source == "wos":
            use_cols = ["C3", "LCS", "TC"]
        elif self._source == "cssci":
            use_cols = ["C3", "LCS"]
        else:
            raise ValueError("Invalid source type")
        return self.generate_df_factory(use_cols, "C3", "; ")

    def generate_journal_df(self) -> pd.DataFrame:
        """Return journal DataFrame."""
        if self._source in ["wos", "scopus"]:
            use_cols = ["SO", "LCS", "TC"]
        elif self._source == "cssci":
            use_cols = ["SO", "LCS"]
        else:
            raise ValueError("Invalid source type")
        return self.generate_df_factory(use_cols, "SO")

    def generate_year_df(self) -> pd.DataFrame:
        """Return publication year DataFrame. Sort by `PY` ascending."""
        use_cols = ["PY"]
        return self.generate_df_factory(use_cols, "PY").sort_values(by="PY")

    def generate_document_type_df(self) -> pd.DataFrame:
        """Return document type DataFrame. Not support CSSCI."""
        assert self._source != "cssci", "CSSCI doesn't have <document type> info"
        use_cols = ["DT"]
        return self.generate_df_factory(use_cols, "DT")

    # def generate_reference_df(self):
    #     """Generate reference DataFrame. The `local` field means whether the reference is in the downloaded records."""
    #     assert self.refs_df is not None, "Argument <refs_df> can't be None"
    #     if self.source == "wos":
    #         keys = ["FAU", "PY", "J9", "VL", "BP", "DI", "local"]
    #     elif self.source == "cssci":
    #         keys = ["FAU", "TI", "SO", "PY", "VL", "local"]
    #     elif self.source == "scopus":
    #         keys = ["FAU", "TI", "SO", "VL", "BP", "EP", "PY", "local"]
    #     else:
    #         raise ValueError("Invalid source type")
    #     refs_df = (
    #         self.refs_df.groupby(by=keys, dropna=False).size().reset_index(name="Recs")
    #     )
    #     refs_df.insert(len(refs_df.columns) - 1, "local", refs_df.pop("local"))
    #     return refs_df.sort_values(by="Recs", ascending=False)

    def write2excel(self, save_path: Path):
        """Write all dataframes to an excel file. Each dataframe is a sheet.

        Args:
            save_path: The path to save the excel file. e.g. `.../descriptive_statistics.xlsx`

        Returns:
            An excel file with multiple sheets.
        """
        Path.mkdir(save_path.parent, exist_ok=True)
        with pd.ExcelWriter(save_path) as writer:
            self.generate_record_df().to_excel(
                writer, sheet_name="Records", index=False
            )
            self.generate_author_df().to_excel(writer, sheet_name="Authors")
            self.generate_journal_df().to_excel(writer, sheet_name="Journals")
            self.generate_keyword_df().to_excel(writer, sheet_name="Keywords")
            self.generate_year_df().to_excel(writer, sheet_name="Years")

            if self._source in ["wos", "cssci"]:
                self.generate_institution_df().to_excel(
                    writer, sheet_name="Institutions"
                )
            if self._source in ["wos", "scopus"]:
                self.generate_document_type_df().to_excel(
                    writer, sheet_name="Document Type"
                )
