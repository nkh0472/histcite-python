from histcite.parse_reference import ParseReference


wos_ref_cell = "Bengio Y, 2001, ADV NEUR IN, V13, P932; Chang Y, 2003, IEEE INTERNATIONAL WORKSHOP ON ANALYSIS AND MODELING OF FACE AND GESTURES, P28; Chen Z., 2000, 6 INT C SPOK LANG PR; CORTES C, 1995, MACH LEARN, V20, P273, DOI 10.1007/BF00994018"
cssci_ref = "1.严栋.基于物联网的智慧图书馆.图书馆学刊.2010.32(7)"
scopus_ref = "Negri E, Fumagalli L, Macchi M., A Review of the Roles of Digital Twin in CPS-based Production Systems, Procedia Manufacturing, 11, pp. 939-948, (2017)"


def test_parse_one_ref():
    parsed_wos_ref = ParseReference().parse_one_ref(wos_ref_cell.split(";")[0], "wos")

    assert isinstance(parsed_wos_ref, dict)
    assert parsed_wos_ref["PY"] == "2001"
    assert parsed_wos_ref["J9"] == "ADV NEUR IN"

    parsed_cssci_ref = ParseReference().parse_one_ref(cssci_ref, "cssci")
    assert isinstance(parsed_cssci_ref, dict)
    assert parsed_cssci_ref["FAU"] == "严栋"
    assert parsed_cssci_ref["VL"] == "32(7)"

    parsed_scopus_ref = ParseReference().parse_one_ref(scopus_ref, "scopus")
    assert isinstance(parsed_scopus_ref, dict)
    assert parsed_scopus_ref["FAU"] == "Negri E"
    assert parsed_scopus_ref["SO"] == "Procedia Manufacturing"
    assert parsed_scopus_ref["VL"] == "11"
    assert parsed_scopus_ref["EP"] == "948"


def test_parse_ref_cell():
    parsed_refs_list = list(ParseReference().parse_ref_cell(wos_ref_cell, "wos"))
    assert isinstance(parsed_refs_list, list)
    assert len(parsed_refs_list) == 4
    assert parsed_refs_list[0]["FAU"] == "Bengio Y"
    assert parsed_refs_list[1]["PY"] == "2003"
    assert parsed_refs_list[2]["J9"] == "6 INT C SPOK LANG PR"
    assert parsed_refs_list[3]["VL"] == "20"
