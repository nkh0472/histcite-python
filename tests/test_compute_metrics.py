from pandas.core.frame import DataFrame
from pathlib import Path
from histcite.compute_metrics import ComputeMetrics


def test_write2excel(
    tmp_path: Path,
    wos_docs_df: DataFrame,
    wos_citation_relation: DataFrame,
    cssci_docs_df: DataFrame,
    cssci_citation_relation: DataFrame,
    scopus_docs_df: DataFrame,
    scopus_citation_relation: DataFrame,
):
    d = tmp_path / "sub"
    d.mkdir()
    ComputeMetrics(wos_docs_df, wos_citation_relation, source="wos").write2excel(
        d / "test1.xlsx"
    )

    ComputeMetrics(cssci_docs_df, cssci_citation_relation, source="cssci").write2excel(
        d / "test2.xlsx"
    )

    ComputeMetrics(
        scopus_docs_df, scopus_citation_relation, source="scopus"
    ).write2excel(d / "test3.xlsx")
