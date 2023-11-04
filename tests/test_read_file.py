from pandas.core.frame import DataFrame


def test_read_wos(wos_docs_df: DataFrame):
    assert wos_docs_df.loc[0, "TI"] == "Recurrent neural network based language model"


def test_read_cssci(cssci_docs_df: DataFrame):
    assert cssci_docs_df.loc[0, "TI"] == "近十年我国智慧图书馆研究态势"


def test_read_scopus(scopus_docs_df: DataFrame):
    assert (
        scopus_docs_df.loc[0, "TI"]
        == "Childhood adversities and adult psychopathology in the WHO world mental health surveys"
    )
