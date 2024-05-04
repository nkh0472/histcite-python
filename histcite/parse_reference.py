from typing import Literal

import refparse


def parse_ref(ref: str, source: Literal["wos", "cssci", "scopus"]):
    try:
        parsed = refparse.parse(ref, source)
    except:
        return None
    else:
        if parsed:
            if source == "wos":
                return {
                    "FAU": parsed["author"],
                    "VL": parsed["volume"],
                    "BP": parsed["page"],
                    "PY": parsed["year"],
                    "DI": parsed["doi"],
                }
            elif source == "scopus":
                return {
                    "FAU": parsed["author"],
                    "VL": parsed["volume"],
                    "BP": parsed["page"],
                    "PY": parsed["year"],
                }
            elif source == "cssci":
                return {
                    "FAU": parsed["author"],
                    "TI": parsed["title"],
                    "PY": parsed["year"],
                }
