class Country:
    def __init__(self, file_path):
        self._country_capital = {}
        self._set_capital(file_path)

    def __getitem__(self, country_name):
        return self._country_capital.get(country_name, None)

    def __iter__(self):
        return CountryIterator(self._country_capital)

    def __len__(self):
        return self._length

    def __str__(self):
        return "Country with " + str(self._length) + " items"

    def _set_capital(self, file_path):
        with open(file_path, "r") as file:
            data = file.readlines()

            header = data[0].split(",")
            country_col = header.index("CountryName")
            capital_col = header.index("CapitalName")

            self._country_capital = {
                values[country_col]: values[capital_col]
                for line in data[1:]
                for values in [line.split(",")]
            }

            self._length = len(self._country_capital)


class CountryIterator:
    def __init__(self, country_capital):
        self._country_capital = country_capital
        self._country_list = list(self._country_capital.keys())
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        try:
            country = self._country_list[self._index]
        except IndexError:
            raise StopIteration()
        self._index += 1
        return country
