import os
from importlib.metadata import entry_points
from walrus.country import Country

file_dir = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(file_dir, "data", "country-capitals.csv")
country = Country(file_path)


def _hello():
    return "Hello World"


def hello(language=None, raise_errors=True):
    if language is None:
        return _hello()

    eps = entry_points(group="walrus.hello")
    if len(eps) == 0:
        if raise_errors:
            raise RuntimeError("No plugins for custom languages installed")
        else:
            return None
    else:
        valid_eps = [
            ep for ep in eps if ep.group == "walrus.hello" and ep.name == language
        ]
        if len(valid_eps) == 0 and raise_errors:
            raise RuntimeError(f"Plugin for language {language} not installed")
        else:
            fn = valid_eps[0].load()
            return fn()


def find_capital(country_name, raise_errors=False):
    capital = country[country_name]

    if capital is None:
        if raise_errors:
            raise ValueError(f"Data not found for: {country_name}")
        else:
            return None

    return capital


def get_capital(country_names, raise_errors=False):
    if isinstance(country_names, str):
        return find_capital(country_names, raise_errors)

    else:
        return {
            a_country: find_capital(a_country, raise_errors)
            for a_country in country_names
        }
