import pytest
import pandas as pd
from histcite.compute_metrics import ComputeMetrics


source_type = "cssci"
docs_df_path = "tests/testdata/docs_df.csv"
citation_relationship_path = "tests/testdata/citation_relationship.csv"

docs_df = pd.read_csv(docs_df_path, dtype_backend="pyarrow")
citation_relationship = pd.read_csv(citation_relationship_path, dtype_backend="pyarrow")
cm = ComputeMetrics(docs_df, citation_relationship, source_type)


def test_records_df():
    records_df = cm.generate_record_df()
    assert records_df.loc[0, "SO"] == "图书馆论坛"


def test_author_df():
    author_df = cm.generate_author_df()
    assert author_df.index[0] == "邵波"
    assert author_df.iloc[0, 0] == 17


def test_keyword_df():
    keyword_df = cm.generate_keyword_df()
    assert keyword_df.index[0] == "智慧图书馆"
    assert keyword_df.iloc[0, 0] == 303


def test_institution_df():
    institution_df = cm.generate_institution_df()
    assert institution_df.index[0] == "南京大学信息管理学院"
    assert institution_df.iloc[0, 0] == 24


def test_journal_df():
    journal_df = cm.generate_journal_df()
    assert journal_df.index[0] == "图书馆学研究"
    assert journal_df.iloc[0, 0] == 72


def test_year_df():
    year_df = cm.generate_year_df()
    assert year_df.index[0] == 2011
    assert year_df.iloc[0, 0] == 2


def test_document_type_df():
    with pytest.raises(AssertionError) as exeinfo:
        cm.generate_document_type_df()
    assert str(exeinfo.value) == "CSSCI doesn't have <document type> info"
