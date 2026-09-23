import re


PARAMETER_CALL_WITH_DESC_KEYWORD_PATTERN = re.compile(
    r'parameter\(\s*(?:.+?)desc=".+?"(?:.*?)\s*\)'
)

PARAMETER_CALL_WITH_ANONYMOUS_DESC_PATTERN = re.compile(
    r'parameter\(\s*(?:.+?),(?:.+?),\s*"(?:.+?)"(?:.*?)\s*\)'
)


# TODO need to find multiline desc pattern failures


def test_only_raw_strings_in_desc_parameter(latex_file):
    """
    Checks that all parameter calls with a desc parameter correctly use a raw string.
    """

    assert not PARAMETER_CALL_WITH_DESC_KEYWORD_PATTERN.findall(latex_file.contents), (f"{latex_file.path.name} ")

    assert not PARAMETER_CALL_WITH_ANONYMOUS_DESC_PATTERN.findall(latex_file.contents), (f"{latex_file.path.name}")


PARAMETER_CALL_WITH_ESCAPES = re.compile(r'parameter\(\s*.*?r".*?\\\\.*?".*?\s*\)')


def test_no_latex_macro_escaping_in_desc_of_parameter(latex_file):
    """
    Checks that all parameter calls with a desc parameter has no escaped macros in
    the raw string.
    """

    assert not PARAMETER_CALL_WITH_ESCAPES.findall(latex_file.contents), (f"{latex_file.path.name}")
