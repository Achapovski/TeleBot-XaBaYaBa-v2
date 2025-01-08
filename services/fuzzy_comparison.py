from fuzzywuzzy import process


def find_most_similar_options(compared_str: str, options_str: list[str], _min_percent: int = 80,
                              _max_percent: int = 90, _without_percentage: bool = False) -> list[str] | str:
    strings_extract = process.extract(compared_str, options_str, limit=3)

    if strings_extract[0][1] >= _max_percent:
        result = strings_extract[0]
    else:
        result = [string[1] for string in filter(lambda x: x[1] >= _min_percent, strings_extract)]

    if _without_percentage:
        return result[0]
    return result

