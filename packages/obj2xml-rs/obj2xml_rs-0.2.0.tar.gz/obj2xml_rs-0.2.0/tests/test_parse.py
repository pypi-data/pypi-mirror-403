import pytest
import io
from obj2xml_rs import parse, parse_async


def test_parse_simple_string():
    xml = "<root>Hello World</root>"
    result = parse(xml)
    assert result == {"root": "Hello World"}


def test_parse_bytes():
    xml = b"<root>Hello Bytes</root>"
    result = parse(xml)
    assert result == {"root": "Hello Bytes"}


def test_parse_file_like():
    xml = "<root>Hello File</root>"
    f = io.BytesIO(xml.encode("utf-8"))
    result = parse(f)
    assert result == {"root": "Hello File"}


def test_parse_deep_nesting():
    xml = """
    <config>
        <server>
            <host>localhost</host>
            <port>8080</port>
        </server>
    </config>
    """
    result = parse(xml)
    expected = {"config": {"server": {"host": "localhost", "port": "8080"}}}
    assert result == expected


def test_attributes_default():
    xml = '<item id="1" active="true">Content</item>'
    result = parse(xml)

    expected = {"item": {"@id": "1", "@active": "true", "#text": "Content"}}
    assert result == expected


def test_custom_prefix_and_key():
    xml = '<item id="1">Content</item>'
    result = parse(xml, attr_prefix="$", cdata_key="_value")
    expected = {"item": {"$id": "1", "_value": "Content"}}
    assert result == expected


def test_empty_element():
    xml = "<root><empty/></root>"
    result = parse(xml)
    assert result == {"root": {"empty": None}}


def test_force_cdata():
    """Even simple elements become dicts with #text if force_cdata=True"""
    xml = "<root>Value</root>"
    result = parse(xml, force_cdata=True)
    assert result == {"root": {"#text": "Value"}}


def test_implicit_list():
    """Repeated tags should automatically become a list."""
    xml = """
    <root>
        <item>A</item>
        <item>B</item>
    </root>
    """
    result = parse(xml)
    assert result == {"root": {"item": ["A", "B"]}}


def test_force_list():
    """Tags in force_list should be lists even if there is only one."""
    xml = """
    <root>
        <item>Single</item>
    </root>
    """
    result = parse(xml, force_list=["item"])
    assert result == {"root": {"item": ["Single"]}}


def test_force_list_mixed():
    """Test force_list with nested structures."""
    xml = """
    <users>
        <user>
            <name>Alice</name>
        </user>
    </users>
    """

    result = parse(xml, force_list=["user"])
    expected = {"users": {"user": [{"name": "Alice"}]}}
    assert result == expected


def test_cdata_parsing():
    """Content inside CDATA should be preserved correctly."""
    xml = "<root><![CDATA[<markup> is safe]]></root>"
    result = parse(xml)
    assert result == {"root": "<markup> is safe"}


def test_comments():
    """Comments should be ignored by default, parsed if requested."""
    xml = "<root><!-- This is a comment -->Data</root>"

    assert parse(xml) == {"root": "Data"}

    res = parse(xml, process_comments=True)
    assert res["root"]["#text"] == "Data"
    assert "This is a comment" in res["root"]["#comment"]


def test_comments_list():
    """Multiple comments should form a list."""
    xml = """
    <root>
        <!-- C1 -->
        <!-- C2 -->
    </root>
    """
    res = parse(xml, process_comments=True)
    assert res["root"]["#comment"] == [" C1 ", " C2 "]


def test_processing_instruction():
    """Processing instructions should be parsed if encountered."""
    xml = """<root><?xml-stylesheet href="style.css"?></root>"""

    result = parse(xml)
    assert result["root"]["?xml-stylesheet"] == 'href="style.css"'


def test_namespaces_ignored():
    """By default, prefixes are kept as-is strings."""
    xml = '<root xmlns:ns="http://example.com"><ns:item>1</ns:item></root>'
    result = parse(xml, process_namespaces=False)

    assert "ns:item" in result["root"]


def test_namespaces_processed():
    """With process_namespaces=True, prefixes are expanded to URIs."""
    xml = '<root xmlns:ns="http://foo"><ns:item>1</ns:item></root>'
    result = parse(xml, process_namespaces=True, namespace_separator="|")

    root = result["root"]
    assert root["http://foo|item"] == "1"


def test_default_namespace():
    xml = '<root xmlns="http://default"><item>1</item></root>'
    result = parse(xml, process_namespaces=True, namespace_separator="|")

    key = "http://default|root"
    assert key in result
    assert result[key]["http://default|item"] == "1"


def test_strip_whitespace():
    xml = "<root>   Content   </root>"

    assert parse(xml) == {"root": "Content"}

    assert parse(xml, strip_whitespace=False) == {"root": "   Content   "}


def test_malformed_xml():
    xml = "<root><unclosed></root>"
    with pytest.raises(ValueError, match="XML Parse Error"):
        parse(xml)


def test_invalid_input_type():
    with pytest.raises(TypeError):
        parse(123)


@pytest.mark.asyncio
async def test_parse_async():
    xml = "<root>Async</root>"
    result = await parse_async(xml)
    assert result == {"root": "Async"}
