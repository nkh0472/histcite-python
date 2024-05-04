from pathlib import Path

import pytest

from histcite.read_file import ReadCssciFile, ReadFile, ReadScopusFile, ReadWosFile


class TestReadWosFile:
    test_corresponding_author_data = [
        (
            "Ledgerwood, A (corresponding author), Univ Calif Davis, Dept Psychol, Davis, CA 95616 USA.",
            "Ledgerwood, A",
        )
    ]

    test_country_data = [
        (
            "[Mikolov, Tomas; Karafiat, Martin; Burget, Lukas; Cernocky, Jan Honza] Brno Univ Technol, Speech FIT, Brno, Czech Republic",
            "Czech Republic",
        ),
        (
            "[Diamond, Steven] Stanford Univ, Dept Comp Sci, Stanford, CA 94305 USA; Stanford Univ, Dept Elect Engn, Stanford, CA 94305 USA",
            "USA",
        ),
    ]

    test_sub_institution_data = [
        (
            "[Sundermeyer, Martin; Schlueter, Ralf; Ney, Hermann] Rhein Westfal TH Aachen, Dept Comp Sci, Aachen, Germany",
            "Rhein Westfal TH Aachen, Dept Comp Sci",
        ),
        (
            "[Dauphin, Yann N.; Fan, Angela; Auli, Michael; Grangier, David] Facebook AI Res, Menlo Pk, CA 94025 USA",
            "Facebook AI Res",
        ),
    ]

    @pytest.mark.parametrize("input, expected", test_corresponding_author_data)
    def test_extract_corresponding_author(self, input, expected):
        assert ReadWosFile.extract_corresponding_author(input) == expected

    @pytest.mark.parametrize("input, expected", test_country_data)
    def test_extract_country(self, input, expected):
        assert ReadWosFile.extract_country(input) == expected

    @pytest.mark.parametrize("input, expected", test_sub_institution_data)
    def test_extract_sub_institution(self, input, expected):
        assert ReadWosFile.extract_sub_institution(input) == expected

    def test_parse_wos_file(self):
        file_path = Path("tests/testdata/savedrecs.txt")
        df = ReadWosFile.read_wos_file(file_path)
        assert "I2" in df.columns.tolist()
        assert df.shape[0] == 300


class TestReadCssciFile:
    test_org_data = [
        (
            "[谭春辉]华中师范大学.信息管理学院/[周一夫]华中师范大学.信息管理学院",
            "华中师范大学.信息管理学院",
        )
    ]

    @pytest.mark.parametrize("input, expected", test_org_data)
    def test_extract_org(self, input, expected):
        assert ReadCssciFile.extract_org(input) == expected

    def test_read_cssci_file(self):
        file_path = Path("tests/testdata/LY_20230630122752.txt")
        df = ReadCssciFile.read_cssci_file(file_path)
        assert df.shape[0] == 318


class TestReadScopusFile:
    def test_read_scopus_file(self):
        file_path = Path("tests/testdata/scopus.csv")
        df = ReadScopusFile.read_scopus_file(file_path)
        assert df.shape[0] == 300


class TestReadFile:
    folder_path = Path("tests/testdata")
    read = ReadFile(folder_path, "wos")

    def test_obtain_file_path_list(self):
        assert len(self.read.obtain_file_path_list()) == 1
