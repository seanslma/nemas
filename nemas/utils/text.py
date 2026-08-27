def to_lowercase(
    s: str | list[str] | dict[str],
    dict_values: bool = False,
) -> str | list[str] | dict[str]:
    """
    Convert string to lowercase

    Parameters:
    -----------
    s : str | list[str] | dict[str]
        The input string
    dict_values : bool, optional
        If True, convert the values of a dictionary to lowercase as well.

    Returns:
    -----------
        str | list[str] | dict[str]
        The lowercase version of the input string, list of strings, or dictionary.
    """
    if s is None:
        return None
    if isinstance(s, str):
        return s.lower()
    elif isinstance(s, list):
        if isinstance(s[0], str):
            return [item.lower() for item in s]
        elif isinstance(s[0], tuple):
            return [(item[0].lower(),) + item[1:] for item in s]
        else:
            return s
    elif isinstance(s, dict):
        if dict_values:
            first_value = next(iter(s.values()))
            if isinstance(first_value, list):
                return {k.lower(): to_lowercase(v) for k, v in s.items()}
            elif isinstance(first_value, dict):
                return {
                    k.lower(): {key.lower(): val for key, val in v.items()}
                    for k, v in s.items()
                }
            elif isinstance(first_value, str):
                return {k.lower(): v.lower() for k, v in s.items()}
            else:
                return {k.lower(): v for k, v in s.items()}
        else:
            return {k.lower(): v for k, v in s.items()}
    else:
        raise TypeError(f'Invalid type for `s`: {type(s)}. Must be str, list, or dict.')


def to_uppercase(
    s: str | list[str],
    dict_values: bool = False,
) -> str | list[str]:
    """
    Convert string to uppercase

    Parameters:
    -----------
    s : str | list[str] | dict[str]
        The input string
    dict_values : bool, optional
        If True, convert the values of a dictionary to uppercase as well.

    Returns:
    -----------
        str | list[str] | dict[str]
        The uppercase version of the input string, list of strings, or dictionary.
    """
    if s is None:
        return None
    elif isinstance(s, str):
        return s.upper()
    elif isinstance(s, list):
        if isinstance(s[0], str):
            return [item.upper() for item in s]
        elif isinstance(s[0], tuple):
            return [(item[0].upper(),) + item[1:] for item in s]
        else:
            return s
    elif isinstance(s, dict):
        if dict_values:
            first_value = next(iter(s.values()))
            if isinstance(first_value, list):
                return {k.upper(): to_uppercase(v) for k, v in s.items()}
            elif isinstance(first_value, dict):
                return {
                    k.upper(): {key.upper(): val for key, val in v.items()}
                    for k, v in s.items()
                }
            elif isinstance(first_value, str):
                return {k.upper(): v.upper() for k, v in s.items()}
            else:
                return {k.upper(): v for k, v in s.items()}
        else:
            return {k.upper(): v for k, v in s.items()}
    else:
        raise TypeError(f'Invalid type for `s`: {type(s)}. Must be str, list, or dict.')


if __name__ == '__main__':
    data = {'KEY_ONE': 'X', 'KEY_TWO': 'STILL_UPPER'}
    result = to_lowercase(data, dict_values=True)
    print(result)
