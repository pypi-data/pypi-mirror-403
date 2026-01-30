from pythonmentor.models.model import build_content


def test_build_content_includes_stripped_parts():
    content = build_content("  Q?  ", "  A!  ", "  Do it  ")

    assert "Do it" in content
    assert "Q?" in content
    assert "A!" in content
    assert "Return ONLY valid JSON" in content
    assert "JSON schema" in content
