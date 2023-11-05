from pathlib import Path
from typing import Literal

import pytest

from histcite.read_file import ReadFile
from histcite.process_file import ProcessFile


def obtain_docs_df(source: Literal["wos", "cssci", "scopus"]):
    folder_path = Path("tests/testdata")
    reader = ReadFile(folder_path, source)
    docs_df = reader.read_all()
    return docs_df


@pytest.fixture(scope="session")
def wos_docs_df():
    return obtain_docs_df("wos")


@pytest.fixture(scope="session")
def cssci_docs_df():
    return obtain_docs_df("cssci")


@pytest.fixture(scope="session")
def scopus_docs_df():
    return obtain_docs_df("scopus")


def obtain_citation_relationship(source: Literal["wos", "cssci", "scopus"]):
    docs_df = obtain_docs_df(source)
    process = ProcessFile(docs_df, source)
    refs_df = process.extract_reference()
    citation_relationship = process.process_citation(refs_df)
    return citation_relationship


@pytest.fixture(scope="session")
def wos_citation_relationship():
    return obtain_citation_relationship("wos")


@pytest.fixture(scope="session")
def cssci_citation_relationship():
    return obtain_citation_relationship("cssci")


@pytest.fixture(scope="session")
def scopus_citation_relationship():
    return obtain_citation_relationship("scopus")
