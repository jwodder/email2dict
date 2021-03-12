from typing import Dict
import pytest
from mailbits import ContentType


@pytest.mark.parametrize(
    "s,ct",
    [
        ("text/plain", ContentType("text", "plain", {})),
        ("TEXT/PLAIN", ContentType("text", "plain", {})),
        (
            "text/plain; charset=utf-8",
            ContentType("text", "plain", {"charset": "utf-8"}),
        ),
        (
            'text/plain; charset="utf-8"',
            ContentType("text", "plain", {"charset": "utf-8"}),
        ),
        (
            "text/markdown; charset=utf-8; variant=GFM",
            ContentType("text", "markdown", {"charset": "utf-8", "variant": "GFM"}),
        ),
        (
            'text/plain; charset="utf-\u2603"',
            ContentType("text", "plain", {"charset": "utf-\u2603"}),
        ),
        (
            "text/plain; charset*=utf-8''utf-%E2%98%83",
            ContentType("text", "plain", {"charset": "utf-\u2603"}),
        ),
    ],
)
def test_parse_content_type(s: str, ct: ContentType) -> None:
    assert ContentType.parse(s) == ct


@pytest.mark.parametrize(
    "s",
    [
        "text",
        "text/",
        "/plain",
        "text/plain, charset=utf-8",
    ],
)
def test_parse_content_type_error(s: str) -> None:
    with pytest.raises(ValueError) as excinfo:
        ContentType.parse(s)
    assert str(excinfo.value) == s


@pytest.mark.parametrize(
    "maintype,subtype,params,ct",
    [
        ("text", "plain", {}, "text/plain"),
        ("TEXT", "PLAIN", {}, "TEXT/PLAIN"),
        ("text", "plain", {"charset": "utf-8"}, 'text/plain; charset="utf-8"'),
        ("text", "plain", {"name": "résumé.txt"}, 'text/plain; name="résumé.txt"'),
        ("text", "plain", {"name": 'foo"bar'}, 'text/plain; name="foo\\"bar"'),
        (
            "text",
            "markdown",
            {"charset": "utf-8", "variant": "GFM"},
            'text/markdown; charset="utf-8"; variant="GFM"',
        ),
    ],
)
def test_assemble_content_type(
    maintype: str, subtype: str, params: Dict[str, str], ct: str
) -> None:
    assert str(ContentType(maintype, subtype, params)) == ct


@pytest.mark.parametrize(
    "maintype,subtype",
    [
        ("text/plain", "plain"),
        ("text", ""),
        ("text/", "plain"),
    ],
)
def test_assemble_content_type_error(maintype: str, subtype: str) -> None:
    with pytest.raises(ValueError) as excinfo:
        str(ContentType(maintype, subtype))
    assert str(excinfo.value) == f"{maintype}/{subtype}"
