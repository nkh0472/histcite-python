from pandas.core.frame import DataFrame


def test_process_wos(wos_citation_relationship: DataFrame):
    assert wos_citation_relationship.shape == (300, 5)
    assert wos_citation_relationship.loc[0, "LCR"] == 0
    assert wos_citation_relationship.loc[1, "LCS"] == 4


def test_process_cssci(cssci_citation_relationship: DataFrame):
    assert cssci_citation_relationship.shape == (318, 5)
    assert cssci_citation_relationship.loc[0, "LCR"] == 5
    assert cssci_citation_relationship.loc[1, "LCS"] == 1


def test_process_scopus(scopus_citation_relationship: DataFrame):
    assert scopus_citation_relationship.shape == (300, 5)
    assert scopus_citation_relationship.loc[0, "LCR"] == 0
    assert scopus_citation_relationship.loc[1, "LCS"] == 0
