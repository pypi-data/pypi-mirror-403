import obj2xml_rs

def test_basic_roundtrip():
    data = {"root": {"@id": "1", "content": "Hello"}}
    xml = obj2xml_rs.unparse(data)
    result = obj2xml_rs.parse(xml)
    assert result == data

def test_list_roundtrip():
    # Note: We must use force_list on parse to ensure single-item lists come back as lists
    data = {"root": {"item": ["A", "B"]}}
    xml = obj2xml_rs.unparse(data)
    result = obj2xml_rs.parse(xml) # Implicit list detection handles >1 items automatically
    assert result == data

def test_attributes_and_text():
    data = {"root": {"@id": "1", "#text": "Value"}}
    xml = obj2xml_rs.unparse(data)
    result = obj2xml_rs.parse(xml)
    assert result == data

def test_mixed_types_roundtrip():
    # Note: XML loses type information (everything becomes string).
    # This test verifies the structure, but expects strings back.
    data = {"root": {"val": 100, "flag": True}}
    xml = obj2xml_rs.unparse(data)

    result = obj2xml_rs.parse(xml)
    # Expect stringified values back
    assert result == {"root": {"val": "100", "flag": "true"}}
