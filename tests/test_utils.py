from utils import color_for_count, valid_text

def test_color_for_count():
    assert color_for_count(10).startswith("#")
    assert color_for_count(250) == "#ffb703"
    assert color_for_count(300) == "#e63946"

def test_valid_text():
    assert valid_text("ok")
    assert not valid_text("")
    assert not valid_text(" " * 3)
    assert not valid_text("a" * 281)
