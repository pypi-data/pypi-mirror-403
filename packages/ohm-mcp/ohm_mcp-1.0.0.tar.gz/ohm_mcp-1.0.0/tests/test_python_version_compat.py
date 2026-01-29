"""
Unit tests for python_version_compat feature detection and compatibility helpers.
"""

from ohm_mcp.refactoring.python_version_compat import (
    detect_version_specific_features,
)


def _feature_names(features):
    return {feature["feature_name"] for feature in features}


def test_detect_walrus_operator():
    code = """
def process(items):
    if (n := len(items)) > 0:
        return n
    return 0
""".strip()
    features = detect_version_specific_features(code)
    assert "Walrus Operator" in _feature_names(features)


def test_detect_match_statement():
    code = """
def handle(value):
    match value:
        case 0:
            return 0
        case _:
            return 1
""".strip()
    features = detect_version_specific_features(code)
    assert "Match Statement" in _feature_names(features)


def test_detect_union_type_syntax():
    code = """
def parse(value: int | str) -> None:
    return None
""".strip()
    features = detect_version_specific_features(code)
    assert "Union Type Syntax" in _feature_names(features)


def test_detect_exception_groups():
    code = """
def run():
    try:
        raise ExceptionGroup("errors", [ValueError("x")])
    except* ValueError as exc:
        return exc
""".strip()
    features = detect_version_specific_features(code)
    assert "Exception Groups" in _feature_names(features)
