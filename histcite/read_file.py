"""This module used to read files and convert to DataFrame.

Supported file types:
- Web of Science: savedrecs.txt
- CSSCI: LY_.txt
- Scopus: scopus.csv
"""
from pathlib import Path
import re
from typing import Callable, Literal

import pandas as pd


def read_csv_file(file_path: Path, use_cols: list[str], sep: str = ",") -> pd.DataFrame:
    """Read csv file using `pyarrow` backend."""
    try:
        df = pd.read_csv(
            file_path,
            sep=sep,
            header=0,
            on_bad_lines="skip",
            usecols=use_cols,
            dtype_backend="pyarrow",
        )
        return df
    except ValueError:
        raise ValueError(f"File {file_path.name} is not a valid csv file")


class ReadWosFile:
    @staticmethod
    def _extract_first_author(au_field: pd.Series) -> pd.Series:
        return au_field.str.split(pat=";", n=1, expand=True)[0].str.replace(",", "")

    @staticmethod
    def extract_corresponding_authors(entry):
        if pd.isna(entry):
            return []
    
        pattern = r"([^;]+)\s*\(\s*corresponding author\s*\)"
        cau_set = set([
            match.group(1).strip()
            if (match := re.search(pattern, author))
            else author.strip()
            for author in re.split(r";\s*", entry)
        ])
        
        return list(cau_set)
        
    @staticmethod
    def _parse_addr(input_str, is_RP=False):
        # handle <NA>
        input_str = '' if pd.isna(input_str) else input_str
        
        # Parse C1 by default, parse RP if is_RP=True
        pattern = r'\(corresponding author\), (.*?)(?:;|$)' if is_RP else r'\] (.*?)(?:\[|$)'

        matches = re.findall(pattern, input_str)

        i2_set = set()
        co_set = set()

        for address_part in matches:
            lines = map(str.strip, address_part.strip().split(';'))

            for line in lines:
                if ',' in line:
                    fields = [item.strip() for item in re.split(',', line)]

                    subdivision = ', '.join(fields[:2]) if len(fields) > 3 else fields[0]
                    i2_set.add(subdivision)

                    country = fields[-1].rstrip('.')
                    co_set.add(country)

        return list(i2_set), list(co_set)


    @staticmethod
    def read_wos_file(file_path: Path) -> pd.DataFrame:
        """Read Web of Science file and return dataframe.

        Args:
            file_path: Path of a Web of Science file. File name is similar to `savedrecs.txt`.
        """
        use_cols = [
            "AU",
            "TI",
            "SO",
            "DT",
            "CR",
            "DE",
            "C3",
            "NR",
            "TC",
            "J9",
            "PY",
            "VL",
            "BP",
            "DI",
            "UT",
            "C1",
            "RP",
            "EM",
        ]
        df = read_csv_file(file_path, use_cols, "\t")
        df.insert(1, "FAU", ReadWosFile._extract_first_author(df["AU"]))
        df["CAU"] = df["RP"].apply(ReadWosFile.extract_corresponding_authors)
        
        # parse Institution with Subdivision ('I2') and Country ('CO') from C1 column by default, same as the original Histcite
        # df[["I2", "CO"]] = df["RP"].apply(lambda x: pd.Series(ReadWosFile._parse_addr(x, True)))
        df[["I2", "CO"]] = df["C1"].apply(lambda x: pd.Series(ReadWosFile._parse_addr(x, False)))
        
        df["source file"] = file_path.name
        return df


class ReadCssciFile:
    @staticmethod
    def _extract_org(org_cell: str) -> str:
        org_set = set(re.findall(r"](.*?)(?:/|$)", org_cell))
        org_list = [i.replace(".", "") for i in org_set]
        return "; ".join(org_list)

    @staticmethod
    def read_cssci_file(file_path: Path) -> pd.DataFrame:
        """Read CSSCI file and return dataframe. Use `WOS` fields to replace original fields.

        Args:
            file_path: Path of a CSSCI file. File name is similar to `LY_.txt`.
        """
        with open(file_path, "r") as f:
            text = f.read()

        body_text = text.split("\n\n\n", 1)[1]
        contents = {}
        original_fields = [
            "来源篇名",
            "来源作者",
            "基    金",
            "期    刊",
            "机构名称",
            "第一作者",
            "年代卷期",
            "关 键 词",
            "参考文献",
        ]
        for field in original_fields:
            if field != "参考文献":
                field_pattern = f"【{field}】(.*?)\n"
                contents[field] = re.findall(field_pattern, body_text)
            else:
                field_pattern = "【参考文献】\n(.*?)\n?" + "-" * 5
                contents[field] = re.findall(field_pattern, body_text, flags=re.S)

        df = pd.DataFrame.from_dict(contents)
        # Rename columns
        column_mapping = {
            "来源篇名": "TI",
            "来源作者": "AU",
            "基    金": "FU",
            "期    刊": "SO",
            "机构名称": "C3",
            "第一作者": "FAU",
            "年代卷期": "PY&VL&BP&EP",
            "关 键 词": "DE",
            "参考文献": "CR",
        }
        df.rename(columns=column_mapping, inplace=True)

        df["AU"] = df["AU"].str.replace("/", "; ")
        df["DE"] = df["DE"].str.replace("/", "; ")
        df["PY"] = df["PY&VL&BP&EP"].str.extract(r"^(\d{4}),", expand=False)
        df["C3"] = df["C3"].apply(ReadCssciFile._extract_org)
        df["CR"] = df["CR"].str.replace("\n", "; ")
        df["NR"] = df["CR"].str.count("; ") + 1
        df.insert(2, "FAU", df.pop("FAU"))
        df["source file"] = file_path.name
        return df


class ReadScopusFile:
    @staticmethod
    def read_scopus_file(file_path: Path) -> pd.DataFrame:
        """Read Scopus file and return dataframe. Use `WOS` fields to replace original fields.

        Args:
            file_path: Path of a Scopus file. File name is similar to `scopus.csv`.
        """
        use_cols = [
            "Authors",
            "Author full names",
            "Title",
            "Year",
            "Source title",
            "Volume",
            "Issue",
            "Page start",
            "Page end",
            "Cited by",
            "DOI",
            "Author Keywords",
            "References",
            "Document Type",
            "EID",
        ]

        df = read_csv_file(file_path, use_cols)
        # Rename columns
        column_mapping = {
            "Authors": "AU",
            "Title": "TI",
            "Year": "PY",
            "Source title": "SO",
            "Volume": "VL",
            "Issue": "IS",
            "Page start": "BP",
            "Page end": "EP",
            "Cited by": "TC",
            "DOI": "DI",
            "Author Keywords": "DE",
            "References": "CR",
            "Document Type": "DT",
        }
        df.rename(columns=column_mapping, inplace=True)

        df["NR"] = df["CR"].str.count("; ")
        df.insert(1, "FAU", df["AU"].str.split(pat=";", n=1, expand=True)[0])
        df["source file"] = file_path.name
        return df


class ReadFile:
    """Read files in the folder path and return a concated dataframe."""

    def __init__(self, folder_path: Path, source: Literal["wos", "cssci", "scopus"]):
        """
        Args:
            folder_path: The folder path of raw files.
            source: Data source. `wos`, `cssci` or `scopus`.
        """
        self._folder_path: Path = folder_path
        self._source: Literal["wos", "cssci", "scopus"] = source
        try:
            self._file_path_list: list[Path] = self._obtain_file_path_list()
        except FileNotFoundError:
            raise FileNotFoundError(f"{folder_path} 文件夹不存在")

    def _obtain_file_path_list(self) -> list[Path]:
        if self._source == "wos":
            file_name_list = [
                i for i in self._folder_path.iterdir() if i.name.startswith("savedrecs")
            ]
        elif self._source == "cssci":
            file_name_list = [
                i for i in self._folder_path.iterdir() if i.name.startswith("LY_")
            ]
        elif self._source == "scopus":
            file_name_list = [
                i for i in self._folder_path.iterdir() if i.name.startswith("scopus")
            ]
        else:
            raise ValueError("Invalid data source")
        file_name_list.sort()
        return file_name_list

    def _concat_df(
        self, read_file_func: Callable[[Path], pd.DataFrame]
    ) -> pd.DataFrame:
        file_count = len(self._file_path_list)
        if file_count > 1:
            return pd.concat(
                [read_file_func(file_path) for file_path in self._file_path_list],
                ignore_index=True,
            )
        elif file_count == 1:
            return read_file_func(self._file_path_list[0])
        else:
            raise FileNotFoundError("No valid file in the folder")

    def read_all(self) -> pd.DataFrame:
        """Concat multi dataframe and drop duplicate rows."""

        def drop_duplicate_rows():
            """
            if wos, drop duplicate rows by `UT`.

            if cssci, drop duplicate rows by `TI` and `FAU`.

            if scopus, drop duplicate rows by `EID`.
            """
            if self._source == "wos":
                check_cols = ["UT"]
            elif self._source == "cssci":
                check_cols = ["TI", "FAU"]
            elif self._source == "scopus":
                check_cols = ["EID"]
            else:
                raise ValueError("Invalid data source")
            original_num = docs_df.shape[0]
            try:
                docs_df.drop_duplicates(
                    subset=check_cols, ignore_index=True, inplace=True
                )
            except Exception:
                print(f"共读取 {original_num} 条数据")
            else:
                current_num = docs_df.shape[0]
                print(f"共读取 {original_num} 条数据，去重后剩余 {current_num} 条")

        if self._source == "wos":
            docs_df = self._concat_df(ReadWosFile.read_wos_file)
            docs_df = docs_df.astype({"PY": "string[pyarrow]", "BP": "string[pyarrow]"})
        elif self._source == "cssci":
            docs_df = self._concat_df(ReadCssciFile.read_cssci_file)
        elif self._source == "scopus":
            docs_df = self._concat_df(ReadScopusFile.read_scopus_file)
        else:
            raise ValueError("Invalid data source")
        drop_duplicate_rows()
        docs_df.insert(0, "doc_id", docs_df.index)
        return docs_df
