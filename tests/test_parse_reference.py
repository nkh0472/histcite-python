from histcite.parse_reference import parse_ref

wos_ref = "Bengio Y, 2001, ADV NEUR IN, V13, P932"
cssci_ref = "1.严栋.基于物联网的智慧图书馆.图书馆学刊.2010.32(7)"
scopus_ref = "Foster E.D., Deardorff A., Open science framework (OSF), Journal of the Medical Library Association, 105, 2, (2017)"


def test_parse_ref():
    parsed_wos_ref = parse_ref(wos_ref, "wos")
    assert isinstance(parsed_wos_ref, dict)
    assert parsed_wos_ref["FAU"] == "Bengio Y"
    assert parsed_wos_ref["VL"] == "13"

    parsed_scopus_ref = parse_ref(scopus_ref, "scopus")
    assert isinstance(parsed_scopus_ref, dict)
    assert parsed_scopus_ref["FAU"] == "Foster E.D., Deardorff A."
    assert parsed_scopus_ref["VL"] == "105"

    parsed_cssci_ref = parse_ref(cssci_ref, "cssci")
    assert isinstance(parsed_cssci_ref, dict)
    assert parsed_cssci_ref["FAU"] == "严栋"
    assert parsed_cssci_ref["PY"] == "2010"
