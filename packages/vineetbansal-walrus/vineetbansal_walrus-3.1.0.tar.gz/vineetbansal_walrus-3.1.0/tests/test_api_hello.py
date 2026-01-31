from walrus.api import hello


def test_hello():
    assert hello() == "Hello World"


def test_hello_es():
    assert hello("es") == "Hola World"
