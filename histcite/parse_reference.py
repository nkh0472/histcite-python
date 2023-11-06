"""This module is used to parse reference.

Supported source type:
- Web of Science
- CSSCI
- Scopus
"""
import re
from typing import Any, Iterator, Literal, NamedTuple, Optional


class WosField(NamedTuple):
    FAU: Optional[str]
    PY: Optional[str]
    J9: Optional[str]
    VL: Optional[str]
    BP: Optional[str]
    DI: Optional[str]


class CSSCIField(NamedTuple):
    FAU: Optional[str]
    TI: Optional[str]
    SO: Optional[str]
    PY: Optional[str]
    VL: Optional[str]


class ScopusField(NamedTuple):
    FAU: Optional[str]
    TI: Optional[str]
    SO: Optional[str]
    VL: Optional[str]
    IS: Optional[str]
    BP: Optional[str]
    EP: Optional[str]
    PY: Optional[str]


class ParseReference:
    @staticmethod
    def _parse_wos_ref(ref: str) -> Optional[WosField]:
        """Parse reference from Web of Science.

        Args:
            ref: A reference string. e.g. `CORTES C, 1995, MACH LEARN, V20, P273, DOI 10.1007/BF00994018`

        Returns:
            A namedtuple of reference fields.
        """
        # Refs contain another language except english or AU is anonymous
        if re.search(r"[\[\]]", ref):
            return None

        # Don't parse patent
        if "Patent No." in ref:
            return None

        FAU, PY, J9, VL, BP, DI = None, None, None, None, None, None
        if ", DOI " in ref:
            # Contain only one DOI
            if "DOI [" not in ref:
                DI_match = re.search(r"DOI (10.*)$", ref)
                DI = DI_match[1] if DI_match else None
            # Contain multi DOIs
            else:
                DI_match = re.search(r"DOI \[(.*)\]", ref)
                DI = DI_match[1] if DI_match else None
            ref = re.sub(r", DOI.*", "", ref)

        BP_match = re.search(r", [Pp]([A-Za-z]?\d+)$", ref)
        if BP_match:
            BP = BP_match[1]
            ref = re.sub(r", [Pp][A-Za-z]?\d+", "", ref)

        ref = re.sub(r"[,\.] PROCEEDINGS(?=, )", "", ref, flags=re.I)
        if VL_match := re.search(r", V([\d-]+)$", ref):
            VL = VL_match[1]
            ref = re.sub(r", V[\d-]+$", "", ref)

        elif re.search(r", VOL[s\.]? ", ref, re.I):
            VL_match = re.search(r", VOL[s\.]? ([\w\- ]+)$", ref, re.I)
            VL = VL_match[1] if VL_match else None
            ref = re.sub(r", VOL.*", "", ref, flags=re.I)

        elif VL_match := re.search(r"(?<=[A-Z\.]), V([\w\. ]+)$", ref):
            VL = VL_match[1]
            ref = re.sub(r"(?<=[A-Z\.]), V[\w\. ]+$", "", ref)

        else:
            pass

        dot_count = ref.count(", ")
        if dot_count == 2:
            FAU, PY, J9 = ref.split(", ")
            if not re.match(r"^\d{4}$", PY):
                return None
        elif dot_count > 2:
            PY_pattern = r", (\d{4}), "
            if re.search(PY_pattern, ref):
                FAU, PY, J9 = re.split(PY_pattern, ref, 1)
        else:
            return None

        if DI is not None:
            DI = DI.lower()
            if len(re.findall(", ", DI)) == 1:
                try:
                    DI1, DI2 = DI.replace("doi ", "").split(", ")
                except:
                    return None
                if DI1 == DI2:
                    DI = DI1
                else:
                    DI = None

        return WosField(FAU, PY, J9, VL, BP, DI)

    @staticmethod
    def _parse_cssci_ref(ref: str) -> Optional[CSSCIField]:
        """Parse reference from CSSCI. Only parse references in Chinese language.

        Args:
            ref: A reference string. e.g. `1.严栋.基于物联网的智慧图书馆.图书馆学刊.2010.32(7)`

        Returns:
            A namedtuple of reference fields.
        """
        dot_pattern = re.compile(
            r"(?<!\d)\.(?!\d)|(?<=\d)\.(?!\d)|(?<!\d)\.(?=\d)|(?<=\d{4})\.(?=\d)|(?<=\d)\.(?=\d{4})"
        )

        if re.search(r"[\u4e00-\u9fa5]", ref):
            dot_count = len(dot_pattern.findall(ref))

            if re.search(r"[^\d]\.{2,}", ref):
                return None

            # Dissertation
            elif ":学位论文." in ref:
                try:
                    _, FAU, TI, other = ref.split(".")
                except:
                    return None
                else:
                    TI = TI.replace(":学位论文", "")
                    SO, PY = other.split(",")
                    PY = PY.split(":")[0]
                    return CSSCIField(FAU, TI, SO, PY, None)

            # Country standard
            elif "GB/T" in ref:
                return None
                # if ref[-3:] == "出版社":
                #     _, FAU, other = ref.split(".", 2)
                #     TI, SO = other.rsplit(".", 1)
                #     return CssciField(FAU, TI, SO, None, None)
                # else:
                #     _, FAU, TI = ref.split(".", 2)
                #     return CssciField(FAU, TI, None, None, None)

            # Standard
            elif re.search(r":DB\d{2}/T", ref):
                return None
                # _, FAU, other = ref.split(".", 2)
                # TI, PY = other.rsplit(".", 1)
                # return CssciField(FAU, TI, None, PY, None)

            # Newspaper
            elif re.search(r"\.\d{1,2}\.\d{1,2}(?:\(|$)", ref):
                try:
                    _, FAU, TI, SO, other = re.split(dot_pattern, ref, 4)
                except:
                    return None
                else:
                    return CSSCIField(FAU, TI, SO, None, None)

            # Patent1
            elif re.search(r"\.CN\d{9}[A-Z]$", ref):
                return None
                # TI = ref.split(".", 1)[1]
                # return CssciField(None, TI, None, None, None)

            # Patent2
            elif re.search(r"^\d+\.一种", ref):
                return None
                # date_pattern = re.compile(r"\d{4}\-\d{1,2}\-\d{1,2}")
                # TI = ref.split(".", 1)[1]
                # date = date_pattern.search(ref)
                # if date:
                #     PY = date[0].split("-")[0]
                # else:
                #     PY = None
                # TI = date_pattern.sub("", TI).strip(".()")
                # return CssciField(None, TI, None, PY, None)

            # Network resource
            elif re.search(r"\.\d{4}$", ref):
                if dot_count == 3:
                    _, FAU, TI, PY = re.split(dot_pattern, ref)
                elif dot_count == 4:
                    _, FAU, TI, SO, PY = re.split(dot_pattern, ref)
                else:
                    return None
                return CSSCIField(FAU, TI, None, PY, None)

            # Journal1
            elif dot_count == 5:
                _, FAU, TI, SO, PY, VL = re.split(dot_pattern, ref)
                return CSSCIField(FAU, TI, SO, PY, VL)

            # Journal2
            elif dot_count == 4:
                _, FAU, TI, SO, _ = re.split(dot_pattern, ref)
                return CSSCIField(FAU, TI, SO, None, None)

            # Book
            elif dot_count == 3:
                _, FAU, TI, SO = re.split(dot_pattern, ref)
                return CSSCIField(FAU, TI, SO, None, None)

            elif dot_count == 2:
                _, FAU, TI = re.split(dot_pattern, ref)
                return CSSCIField(FAU, TI, None, None, None)

            # elif dot_count == 1:
            #     _, TI = re.split(dot_pattern, ref)
            #     return CssciField(None, TI, None, None, None, doc_id)

            else:
                return None
        else:
            return None

    @staticmethod
    def _parse_scopus_ref(ref: str) -> Optional[ScopusField]:
        """Parse reference from Scopus.

        Args:
            ref: A reference string. e.g. `Negri E, Fumagalli L, Macchi M., A Review of the Roles of Digital Twin in CPS-based Production Systems, Procedia Manufacturing, 11, pp. 939-948, (2017)`

        Returns:
            A namedtuple of reference fields.
        """
        if re.search(r"^[^A-Z\*\']", ref):
            return None

        if re.search(r"[\[\]]", ref):
            return None

        if ref.count(", ") < 2:
            return None

        # Publication year
        PY_match = re.search(r", \((\d{4})\)$", ref)
        if PY_match:
            PY = PY_match[1]
            ref = ref.rsplit(", ", 1)[0]
        else:
            return None

        FAU, TI, SO, VL, IS, BP, EP = None, None, None, None, None, None, None
        # Remove version info
        ref = re.sub(r", version [\d\.]+(?=,)", "", ref, flags=re.I)

        # Remove doi info
        ref = re.sub(r", doi:.*(?=,|$)", "", ref, flags=re.I)

        # Remove retrieval info
        ref = re.sub(r"[\.,] Retrieved.*(?=,)", "", ref, flags=re.I)
        ref = re.sub(r", Available from:(?=,)", "", ref, flags=re.I)

        # Page number
        if PP_match := re.search(r"(?:, | \()[Pp]{2}[\.,] ([\w\-]+)\)?", ref):
            PP = PP_match[1]
            try:
                BP, EP = re.split(r"-", PP, 1)
            except:
                BP, EP = None, None
            ref = re.sub(r"(?:, | \()[Pp]{2}.*", "", ref)

        # Volume and Issue
        if VL_IS_match := re.search(r", (\d+\s?[A-Za-z]*, [\w\s\-\.\–]+)$", ref):
            VL, IS = VL_IS_match[1].split(", ")
            ref = ref.rsplit(", ", 2)[0]

        elif IS_match := re.search(r", ([\w-]* ?suppl\.? ?[\w-]*)$", ref, re.I):
            IS = IS_match[1]
            ref = ref.rsplit(", ", 1)[0]

        elif IS_match := re.search(r", (\d* ?PART\.? [A-Z\d]+)$", ref, re.I):
            IS = IS_match[1]
            ref = ref.rsplit(", ", 1)[0]

        elif IS_match := re.search(r", ([Nn]o\. \d+)$", ref):
            IS = IS_match[1]
            ref = ref.rsplit(", ", 1)[0]

        if VL_match := re.search(r", (\d+)$", ref):
            VL = VL_match[1]
            ref = ref.rsplit(", ", 1)[0]

        elif VL_match := re.search(r", ([Vv]ol\. [\w\s\.:]+)$", ref):
            VL = VL_match[1]
            ref = ref.rsplit(", ", 1)[0]

        # Author
        full_name_pattern = r"^(?:[a-zA-Z][a-zA-Z\-\.\']*\s)+[A-Z][a-zA-Z\-\.\']*(, |$)"
        if re.search(r"Et al\.", ref, flags=re.I):
            FAU = ref.split(", ")[0]
            ref = re.sub(r"^.*Et al\.,?\s?", "", ref, flags=re.I)

        elif "., " in ref:
            AU = ref.rsplit("., ", 1)[0]
            if "," in AU:
                FAU = AU.split(", ")[0]
            else:
                FAU = AU + "."
            ref = ref.replace(f"{AU}., ", "")

        elif re.search(r"^(?:[A-Z][a-zA-Z]*\s)+[A-Z][a-zA-Z]*(?=, )", ref):
            FAU = ref.split(", ", 1)[0]
            ref = ref.replace(f"{FAU}, ", "")

        elif re.search(r"^[A-Z-]+, (?=[A-Z])", ref):
            FAU = ref.split(", ", 1)[0]
            ref = ref.replace(f"{FAU}, ", "")

        elif re.search(full_name_pattern, ref):
            FAU = re.split(", ", ref, 1)[0]
            while re.search(full_name_pattern, ref):
                ref = re.sub(full_name_pattern, "", ref, 1)

        else:
            return None

        # Title and Source
        if ref != "":
            comma_pattern = r", (?![^\[]*\]|[^(]*\))"
            comma_count = len(re.findall(comma_pattern, ref))
            if comma_count == 0:
                TI = ref
            elif comma_count == 1:
                TI, SO = re.split(comma_pattern, ref)
            else:
                # Conference ref
                if re.search(
                    r"Conference|Conf\.|Proceeding|Proc\.|Committee|Symposium|Convention|Congress",
                    ref,
                    flags=re.I,
                ):
                    TI, SO = ref.split(", ", 1)

                # Match source
                elif SO_match := re.search(r", ([A-Z\d][\w\s\.\-&:]+)$", ref):
                    SO = SO_match[1]
                    TI = ref.replace(f", {SO}", "")

                # Match title
                elif TI_match := re.search(
                    r"^(([^\.\s]+ ){3,}[^\.\sA-Z]+), [A-Z]", ref
                ):
                    TI = TI_match[1]
                    SO = ref.replace(f"{TI}, ", "")

                elif re.search(r"^[A-Z][^A-Z]+$", ref):
                    TI = ref

                else:
                    return None
        return ScopusField(FAU, TI, SO, VL, IS, BP, EP, PY)

    def parse_one_ref(
        self,
        ref: str,
        source: Literal["wos", "cssci", "scopus"],
        doc_id: Optional[int] = None,
    ) -> Optional[dict[str, Any]]:
        """Parse a raw reference string.

        Args:
            ref: A raw reference string.
            source: Data source. `wos`, `cssci` or `scopus`.
            doc_id: doc_id to which the reference cell belongs. Default None.

        Returns:
            Parsed reference as a dict.
        """

        def tuple2dict(x: Optional[NamedTuple]):
            if x is not None:
                return x._asdict()

        if source == "wos":
            result = tuple2dict(self._parse_wos_ref(ref))
        elif source == "cssci":
            result = tuple2dict(self._parse_cssci_ref(ref))
        elif source == "scopus":
            result = tuple2dict(self._parse_scopus_ref(ref))
        else:
            raise ValueError("Invalid source type")

        if result is not None:
            return {"doc_id": doc_id} | result
        else:
            return None

    def parse_ref_cell(
        self,
        ref_cell: str,
        source: Literal["wos", "cssci", "scopus"],
        doc_id: Optional[int] = None,
    ) -> Iterator[dict[str, Any]]:
        """Parse a reference cell.

        Args:
            ref_cell: A reference cell.
            source: Data source. `wos`, `cssci` or `scopus`.
            doc_id: doc_id to which the reference cell belongs. Default None.

        Returns:
            Generator of parsed references.
        """
        sep = "; "
        try:
            ref_list = re.split(sep, ref_cell)
        except Exception:
            pass
        else:
            for ref in ref_list:
                parsed_ref = self.parse_one_ref(ref, source, doc_id)
                if parsed_ref is not None:
                    yield parsed_ref
