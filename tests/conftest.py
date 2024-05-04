from pathlib import Path

import pytest

from histcite.process_file import BuildCitation, BuildRef
from histcite.read_file import ReadFile


@pytest.fixture(scope="package")
def wos_docs_df():
    folder_path = Path("tests/testdata")
    reader = ReadFile(folder_path, "wos")
    docs_df = reader.read_all()
    return docs_df


@pytest.fixture(scope="package")
def wos_citation_matrix(wos_docs_df):
    refs_df = BuildRef(wos_docs_df, "wos").build()
    citation_matrix = BuildCitation(wos_docs_df, refs_df, "wos").build()
    return citation_matrix
