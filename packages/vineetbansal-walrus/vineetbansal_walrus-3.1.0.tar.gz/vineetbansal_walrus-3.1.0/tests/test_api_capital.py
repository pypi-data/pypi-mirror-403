import pytest
from walrus.api import get_capital


def test_capital_single_correct():
    assert get_capital("Australia") == "Canberra"
    assert get_capital("Australia", raise_errors=True) == "Canberra"


def test_capital_tuple_correct():
    assert get_capital(("Australia", "France")) == {
        "Australia": "Canberra",
        "France": "Paris",
    }
    assert get_capital(("Australia", "France"), raise_errors=True) == {
        "Australia": "Canberra",
        "France": "Paris",
    }


def test_capital_list_correct():
    assert get_capital(["Australia", "France"]) == {
        "Australia": "Canberra",
        "France": "Paris",
    }
    assert get_capital(["Australia", "France"], raise_errors=True) == {
        "Australia": "Canberra",
        "France": "Paris",
    }


def test_capital_single_incorrect():
    assert get_capital("Austraalia") is None
    with pytest.raises(ValueError, match="Data not found for: Austraalia"):
        get_capital("Austraalia", raise_errors=True)


def test_capital_tuple_incorrect():
    assert get_capital(("Australia", "Fraance")) == {
        "Australia": "Canberra",
        "Fraance": None,
    }
    with pytest.raises(ValueError, match="Data not found for: Austraalia"):
        get_capital(("Austraalia", "France"), raise_errors=True)


def test_capital_list_incorrect():
    assert get_capital(["Australia", "Fraance"]) == {
        "Australia": "Canberra",
        "Fraance": None,
    }
    with pytest.raises(ValueError, match="Data not found for: Austraalia"):
        get_capital(["Austraalia", "France"], raise_errors=True)
