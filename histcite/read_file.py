"""This module used to read files and convert to DataFrame.

Supported file types:
- Web of Science: savedrecs.txt
- CSSCI: LY_.txt
- Scopus: scopus.csv
"""

import re
from pathlib import Path
from typing import Callable, Literal, Optional

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
    def extract_first_author(au_field: pd.Series) -> pd.Series:
        return au_field.str.split(pat=";", n=1, expand=True)[0].str.replace(",", "")

    @staticmethod
    def extract_corresponding_authors(entry: Optional[str]) -> Optional[str]:
        """Extract corresponding authors from RP value."""
        pattern = r"(?:^|\.; )(.+?)\s*\(corresponding author\)"
        if entry is not None:
            cau_list = []
            for cau in re.findall(pattern, entry):
                if "; " in cau:
                    cau_list.extend(cau.split("; "))
                else:
                    cau_list.append(cau)
        return "; ".join(set(cau_list))

    @staticmethod
    def extract_co_i2(entry: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """Extract country and institution with subdivision from C1 or RP value"""
        co_value = None
        i2_value = None
        if entry is not None:
            if "corresponding author" in entry:
                pattern = r"\(corresponding author\), (.*?)\.(?=;|$)"
            else:
                pattern = r"\] (.*?)(?=; \[|$)"
            addr_list = re.findall(pattern, entry)
            if len(addr_list) > 0:
                co_set = set()
                i2_set = set()
                for addr in addr_list:
                    parts = addr.split(", ")
                    i2 = ", ".join(parts[:2]) if len(parts) > 3 else parts[0]
                    co = parts[-1]
                    if co[-4:] == " USA":
                        co = "USA"
                    co_set.add(co)
                    i2_set.add(i2)
                co_value = "; ".join(co_set)
                i2_value = "; ".join(i2_set)
        return co_value, i2_value

    @staticmethod
    def read_wos_file(file_path: Path, addr_field: Literal["C1", "RP"]) -> pd.DataFrame:
        """Read Web of Science file and return dataframe.

        Args:
            file_path: Path of a Web of Science file. File name is similar to `savedrecs.txt`.
            addr_field: Which address field to use to extract institution with subdivision and country info.
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
        ]
        df = read_csv_file(file_path, use_cols, "\t")
        df.insert(1, "FAU", ReadWosFile.extract_first_author(df["AU"]))
        df.insert(2, "CAU", df["RP"].apply(ReadWosFile.extract_corresponding_authors))
        df[["CO", "I2"]] = df[addr_field].apply(ReadWosFile.extract_co_i2).apply(pd.Series)
        df["source file"] = file_path.name
        return df


class ReadCssciFile:
    @staticmethod
    def extract_org(org_cell: str) -> str:
        org_set = set(re.findall(r"](.*?)(?:/|$)", org_cell))
        return "; ".join([i.replace(".", "") for i in org_set])

    @staticmethod
    def read_cssci_file(file_path: Path) -> pd.DataFrame:
        """Read CSSCI file and return dataframe. Use `WOS` fields to replace original fields.

        Args:
            file_path: Path of a CSSCI file. File name is similar to `LY_.txt`.
        """
        with open(file_path, "r", encoding="utf-8") as f:
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
        df["C3"] = df["C3"].apply(ReadCssciFile.extract_org)
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

    def __init__(
        self, folder_path: Path, source: Literal["wos", "cssci", "scopus"], addr_field: Literal["C1", "RP"] = "C1"
    ):
        """
        Args:
            folder_path: The folder path of raw files.
            source: Data source. `wos`, `cssci` or `scopus`.
            addr_field: Address field, only for wos source. `C1` or `RP`.
        """
        self.folder_path: Path = folder_path
        self.source: Literal["wos", "cssci", "scopus"] = source
        self.addr_field = addr_field
        try:
            self.file_path_list: list[Path] = self.obtain_file_path_list()
        except FileNotFoundError:
            raise FileNotFoundError(f"{folder_path} 文件夹不存在")

    def obtain_file_path_list(self) -> list[Path]:
        if self.source == "wos":
            file_name_list = [i for i in self.folder_path.iterdir() if i.name.startswith("savedrecs")]
        elif self.source == "cssci":
            file_name_list = [i for i in self.folder_path.iterdir() if i.name.startswith("LY_")]
        elif self.source == "scopus":
            file_name_list = [i for i in self.folder_path.iterdir() if i.name.startswith("scopus")]
        else:
            raise ValueError("Invalid data source")
        file_name_list.sort()
        return file_name_list

    def concat_df(self) -> pd.DataFrame:
        file_count = len(self.file_path_list)
        if file_count > 1:
            if self.source == "wos":
                return pd.concat(
                    [ReadWosFile.read_wos_file(file_path, self.addr_field) for file_path in self.file_path_list],
                    ignore_index=True,
                )
            elif self.source == "cssci":
                return pd.concat(
                    [ReadCssciFile.read_cssci_file(file_path) for file_path in self.file_path_list],
                    ignore_index=True,
                )
            elif self.source == "scopus":
                return pd.concat(
                    [ReadScopusFile.read_scopus_file(file_path) for file_path in self.file_path_list],
                    ignore_index=True,
                )
        elif file_count == 1:
            if self.source == "wos":
                return ReadWosFile.read_wos_file(self.file_path_list[0], self.addr_field)
            elif self.source == "cssci":
                return ReadCssciFile.read_cssci_file(self.file_path_list[0])
            elif self.source == "scopus":
                return ReadScopusFile.read_scopus_file(self.file_path_list[0])
        else:
            raise FileNotFoundError("No valid file in the folder")

    @staticmethod
    def drop_duplicate_rows(docs_df: pd.DataFrame, check_cols: list[str]) -> pd.DataFrame:
        original_num = docs_df.shape[0]
        try:
            docs_df = docs_df.drop_duplicates(subset=check_cols, ignore_index=True)
        except Exception:
            print(f"共读取 {original_num} 条数据")
        else:
            current_num = docs_df.shape[0]
            print(f"共读取 {original_num} 条数据，去重后剩余 {current_num} 条")
        finally:
            return docs_df

    def read_all(self) -> pd.DataFrame:
        """Concat multi dataframe and drop duplicate rows."""
        if self.source == "wos":
            check_cols = ["UT"]
        elif self.source == "cssci":
            check_cols = ["TI", "FAU"]
        elif self.source == "scopus":
            check_cols = ["EID"]

        docs_df = self.concat_df()
        docs_df = self.drop_duplicate_rows(docs_df, check_cols)
        docs_df.insert(0, "doc_id", docs_df.index)
        docs_df = docs_df.convert_dtypes(dtype_backend="pyarrow")
        return docs_df
