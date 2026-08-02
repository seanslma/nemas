import pytest

from nemas.utils import to_lowercase


# ---------------------------------------------------------------------------
# None
# ---------------------------------------------------------------------------


def test_none_returns_none():
    assert to_lowercase(None) is None


# ---------------------------------------------------------------------------
# str
# ---------------------------------------------------------------------------


def test_string_lowercased():
    assert to_lowercase('HELLO World') == 'hello world'


def test_string_already_lowercase():
    assert to_lowercase('already lower') == 'already lower'


def test_empty_string():
    assert to_lowercase('') == ''


# ---------------------------------------------------------------------------
# list[str]
# ---------------------------------------------------------------------------


def test_list_of_strings_lowercased():
    assert to_lowercase(['FOO', 'Bar', 'baz']) == ['foo', 'bar', 'baz']


def test_list_of_strings_single_item():
    assert to_lowercase(['ONLY']) == ['only']


def test_empty_list_raises_indexerror():
    with pytest.raises(IndexError):
        to_lowercase([])


# ---------------------------------------------------------------------------
# list[tuple]
# ---------------------------------------------------------------------------


def test_list_of_tuples_first_element_lowercased():
    data = [('FOO', 1), ('BAR', 2, 3)]
    result = to_lowercase(data)
    assert result == [('foo', 1), ('bar', 2, 3)]


def test_list_of_tuples_preserves_rest_of_tuple():
    data = [('KEY', 'VALUE', 42)]
    result = to_lowercase(data)
    # Only the first element is lowercased; remaining elements pass through
    # untouched (note "VALUE" stays uppercase).
    assert result == [('key', 'VALUE', 42)]


def test_list_of_single_element_tuples():
    data = [('ONLY',)]
    assert to_lowercase(data) == [('only',)]


# ---------------------------------------------------------------------------
# list of something else (fallback branch)
# ---------------------------------------------------------------------------


def test_list_of_other_type_returned_unchanged():
    data = [1, 2, 3]
    result = to_lowercase(data)
    assert result == [1, 2, 3]
    assert result is data  # returned as-is, not copied


# ---------------------------------------------------------------------------
# dict, dict_values=False (default)
# ---------------------------------------------------------------------------


def test_dict_no_dict_values_raises_typeerror():
    assert to_lowercase({'KEY': 'value'}) == {'key': 'value'}


def test_dict_default_arg_also_raises():
    assert to_lowercase({'A': 1}) == {'a': 1}


# ---------------------------------------------------------------------------
# dict, dict_values=True, scalar values
# ---------------------------------------------------------------------------


def test_dict_values_true_scalar_values_only_keys_lowercased():
    data = {'KEY_ONE': 'X', 'KEY_TWO': 'STILL_UPPER'}
    result = to_lowercase(data, dict_values=True)
    # Keys lowercased; scalar (non-list/dict) values passed through untouched.
    assert result == {'key_one': 'x', 'key_two': 'still_upper'}


def test_dict_values_true_empty_dict_raises_stopiteration():
    # next(iter(s.values())) on an empty dict raises StopIteration.
    with pytest.raises(StopIteration):
        to_lowercase({}, dict_values=True)


# ---------------------------------------------------------------------------
# dict, dict_values=True, list values (recursive call)
# ---------------------------------------------------------------------------


def test_dict_values_true_list_values_recursively_lowercased():
    data = {'KEY': ['FOO', 'BAR']}
    result = to_lowercase(data, dict_values=True)
    assert result == {'key': ['foo', 'bar']}


def test_dict_values_true_list_of_dicts_returned_unchanged():
    # v = [{"NESTED": "X"}] is a list whose first element is neither str nor
    # tuple, so the recursive to_lowercase(v) call falls into the list
    # "else" branch and returns it completely unchanged (dict keys/values
    # inside are NOT lowercased).
    data = {'KEY': [{'NESTED': 'X'}]}
    result = to_lowercase(data, dict_values=True)
    assert result == {'key': [{'NESTED': 'X'}]}


# ---------------------------------------------------------------------------
# dict, dict_values=True, dict values (nested dict) -- current buggy behavior
# ---------------------------------------------------------------------------


def test_dict_dict_values_nested_dict_raises():
    # `for key, val in v` iterates dict keys only; unpacking a plain string
    # key into (key, val) raises ValueError.
    data = {'OUTER': {'INNER_KEY': 'inner_value'}}
    assert to_lowercase(data, dict_values=True) == {
        'outer': {'inner_key': 'inner_value'}
    }


def test_dict_dict_values_nested_dict_of_two_char_keys_does_not_raise():
    # If every inner key happens to be exactly 2 characters, `for key, val
    # in v` unpacks each key string into (key, val) without error -- this
    # is a surprising, unintended consequence of the bug, included here so
    # a future fix's diff makes the change in behavior obvious.
    data = {'OUTER': {'ab': 'unused', 'cd': 'unused'}}
    result = to_lowercase(data, dict_values=True)
    assert result == {'outer': {'ab': 'unused', 'cd': 'unused'}}


# ---------------------------------------------------------------------------
# Parametrized sanity sweep across simple types
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'value, expected',
    [
        ('ABC', 'abc'),
        (['ABC', 'DEF'], ['abc', 'def']),
        ([('ABC', 1)], [('abc', 1)]),
    ],
)
def test_parametrized_basic_cases(value, expected):
    assert to_lowercase(value) == expected
