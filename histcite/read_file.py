"""This module used to read files and convert to DataFrame.

Supported file types:
- Web of Science: savedrecs.txt
- CSSCI: LY_.txt
- Scopus: scopus.csv
"""

import re
from pathlib import Path
from typing import Literal, Optional

import pandas as pd


class ReadWosFile:
    @staticmethod
    def extract_corresponding_author(entry: Optional[str]) -> Optional[str]:
        """Extract corresponding author from RP value."""
        if isinstance(entry, str):
            cau_list = []
            pattern = r"(?:^|\.; )(.+?)\s*\(corresponding author\)"
            if match_values := re.findall(pattern, entry):
                for cau in match_values:
                    if "; " in cau:
                        cau_list.extend(cau.split("; "))
                    else:
                        cau_list.append(cau)
                return "; ".join(set(cau_list))

    @staticmethod
    def extract_country(entry: Optional[str]) -> Optional[str]:
        """Extract country info from C1 value."""
        if isinstance(entry, str):
            addr_list = re.findall(r"\] (.*?)(?=;|$)", entry)
            if len(addr_list) > 0:
                country_list = [addr.rsplit(", ", 1)[1] for addr in addr_list]
                country_list = ["USA" if country.endswith(" USA") else country for country in country_list]
                return "; ".join(set(country_list))

    @staticmethod
    def extract_sub_institution(entry: Optional[str]) -> Optional[str]:
        """Extract sub institution from C1 value"""
        if isinstance(entry, str):
            addr_list = re.findall(r"\] (.*?)(?=;|$)", entry)
            if len(addr_list) > 0:
                institution_list = []
                for addr in addr_list:
                    if addr.count(", ") >= 3:
                        institution = ", ".join(addr.split(", ", 2)[:2])
                    else:
                        institution = addr.split(", ", 1)[0]
                    institution_list.append(institution)
                return "; ".join(set(institution_list))

    @staticmethod
    def from_plain_text(file_path: Path, use_cols: list[str]) -> pd.DataFrame:
        with open(file_path, "r") as f:
            text = f.read()

        col_data = {}
        parts = re.split("\n(?=PT )", text)[1:]
        record_num = len(parts)
        for col in use_cols:
            pattern = rf"\n{col} (.*?)\n[A-Z](?:[A-Z]|\d) "
            match_values = re.findall(pattern, text, flags=re.S)
            if len(match_values) != record_num:
                match_values = []
                for part in parts:
                    if match := re.search(pattern, part, flags=re.S):
                        match_values.append(match.group(1))
                    else:
                        match_values.append(None)
            col_data[col] = match_values

        df = pd.DataFrame(col_data)
        df["NR"] = df["NR"].apply(int)
        df["TC"] = df["TC"].apply(int)
        df["AU"] = df["AU"].str.replace(r"\n\s+", "; ", regex=True)
        df["CR"] = df["CR"].str.replace(r"\n\s+", "; ", regex=True)
        df["C1"] = df["C1"].str.replace(r"\.\n\s+", "; ", regex=True).str.rstrip(".")

        df["SO"] = df["SO"].str.replace(r"\n\s+", " ", regex=True)
        df["DE"] = df["DE"].str.replace(r"\n\s+", " ", regex=True)
        df["C3"] = df["C3"].str.replace(r"\n\s+", " ", regex=True)
        return df

    def read_wos_file(self, file_path: Path) -> pd.DataFrame:
        """Read Web of Science file and return dataframe.

        Args:
            file_path: Path of a Web of Science file. File name is similar to `savedrecs.txt`. It can be tab-delimited or plain text format.
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
            "PY",
            "VL",
            "BP",
            "DI",
            "UT",
            "C1",
            "RP",
        ]
        try:
            df = pd.read_csv(file_path, sep="\t", header=0, on_bad_lines="skip", usecols=use_cols)
        except ValueError:
            df = self.from_plain_text(file_path, use_cols)

        df.insert(1, "FAU", df["AU"].str.split(pat=";", n=1).str[0].str.replace(",", ""))
        df.insert(2, "CAU", df["RP"].apply(ReadWosFile.extract_corresponding_author))
        df["CO"] = df["C1"].apply(ReadWosFile.extract_country)
        df["I2"] = df["C1"].apply(ReadWosFile.extract_sub_institution)
        df["source file"] = file_path.name
        return df


class ReadCssciFile:
    @staticmethod
    def extract_org(entry: str) -> str:
        org_list = re.findall(r"](.*?)(?:/|$)", entry)
        return "; ".join(set(org_list))

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
            "年代卷期": "MIX",
            "关 键 词": "DE",
            "参考文献": "CR",
        }
        df.rename(columns=column_mapping, inplace=True)

        df["AU"] = df["AU"].str.replace("/", "; ")
        df["DE"] = df["DE"].str.replace("/", "; ")
        df["PY"] = df["MIX"].str.extract(r"^(\d{4}),")
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
        df = pd.read_csv(file_path, sep=",", header=0, on_bad_lines="skip", usecols=use_cols)
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
        df.insert(1, "FAU", df["AU"].str.split(pat=";", n=1).str[0])
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
        self.folder_path: Path = folder_path
        self.source: Literal["wos", "cssci", "scopus"] = source
        try:
            self.file_path_list: list[Path] = self.obtain_file_path_list()
        except FileNotFoundError:
            raise FileNotFoundError(f"{folder_path} 文件夹不存在")

    def obtain_file_path_list(self) -> list[Path]:
        if self.source == "wos":
            file_name_list = [i for i in self.folder_path.iterdir() if i.name.startswith("savedrecs") and i.suffix == ".txt"]
        elif self.source == "cssci":
            file_name_list = [i for i in self.folder_path.iterdir() if i.name.startswith("LY_") and i.suffix == ".txt"]
        elif self.source == "scopus":
            file_name_list = [i for i in self.folder_path.iterdir() if i.name.startswith("scopus") and i.suffix == ".csv"]
        else:
            raise ValueError("Invalid data source")
        file_name_list.sort()
        return file_name_list

    def read_file(self, file_path: Path):
        if self.source == "wos":
            return ReadWosFile().read_wos_file(file_path)
        elif self.source == "scopus":
            return ReadScopusFile.read_scopus_file(file_path)
        elif self.source == "cssci":
            return ReadCssciFile.read_cssci_file(file_path)

    def concat_files(self):
        file_count = len(self.file_path_list)
        if file_count > 1:
            return pd.concat([self.read_file(file_path) for file_path in self.file_path_list], ignore_index=True)
        elif file_count == 1:
            return self.read_file(self.file_path_list[0])
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
            check_cols = ["FAU", "TI"]
        elif self.source == "scopus":
            check_cols = ["EID"]

        docs_df = self.concat_files()
        assert docs_df is not None, "Something wrong happened when reading files."
        docs_df = self.drop_duplicate_rows(docs_df, check_cols)
        docs_df.insert(0, "node", docs_df.index)
        docs_df = docs_df.convert_dtypes(dtype_backend="pyarrow")
        return docs_df
