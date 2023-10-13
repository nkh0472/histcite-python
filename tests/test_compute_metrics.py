from histcite.compute_metrics import ComputeMetrics


def test_write2excel(
    tmp_path,
    wos_docs_df,
    wos_citation_relationship,
    cssci_docs_df,
    cssci_citation_relationship,
    scopus_docs_df,
    scopus_citation_relationship,
):
    d = tmp_path / "sub"
    d.mkdir()
    ComputeMetrics(wos_docs_df, wos_citation_relationship, "wos").write2excel(
        d / "test1.xlsx"
    )
    ComputeMetrics(
        cssci_docs_df, cssci_citation_relationship, source="cssci"
    ).write2excel(d / "test2.xlsx")
    ComputeMetrics(
        scopus_docs_df, scopus_citation_relationship, source="scopus"
    ).write2excel(d / "test3.xlsx")
