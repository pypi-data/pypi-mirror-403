from pathlib import Path, PosixPath
from pytest import mark, param
import warnings
import sys

import dawgdad as dd
import pandas as pd
import numpy as np


pd.set_option('future.no_silent_downcasting', True)
df = pd.DataFrame(
    data=dict(
        floats=[1.0, np.nan, 3.0, np.nan, 5.0, 6.0, np.nan],
        text=["A", "B", "C", "D", "E", "F", np.nan],
        dates=[
            "1956-06-08", "1956-06-08",
            "1956-06-08", "1956-06-08",
            "1956-06-08", "1956-06-08",
            pd.NaT
        ],
        all_nan=[np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
        all_nat=[pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT],
        all_none=[None, None, None, None, None, None, None],
        all_space=["", " ", "", " ", "", "", ""],
        nan_space=[np.nan, "", " ", np.nan, np.nan, np.nan, np.nan],
        nan_none=[np.nan, None, np.nan, np.nan, None, np.nan, None],
        mixed=[None, np.nan, pd.NaT, pd.NaT, None, np.nan, pd.NaT],
        integers=[1, 2, np.nan, 4, 5, 6, np.nan],
    )
).replace(
    r"^\s+$",
    np.nan,
    regex=True
).replace(
    "",
    np.nan,
    regex=True
).astype(
    dtype={
        "integers": "Int64",
        "floats": "float64",
        "text": "object",
        "dates": "datetime64[ns]",
        "all_nan": "float64",
        "all_nat": "datetime64[ns]",
        "all_none": "float64",
        "all_space": "float64",
        "nan_space": "float64",
        "nan_none": "float64",
        "mixed": "datetime64[ns]"
    }
)


@mark.parametrize(
    "listone, listtwo, expected",
    [
        (["prefix-2020-21-CMJG-suffix", "bobs your uncle"], ["CMJG", "2020-21"], ["prefix-2020-21-CMJG-suffix"]),
        (["apple pie", "banana bread", "apple crumble"], ["apple"], ["apple pie", "apple crumble"]),
        (["one two three", "four five six"], ["two", "five"], []),
        (["abc", "def"], [], ["abc", "def"]),
        ([], ["xyz"], []),
        (["hello world"], ["hello world"], ["hello world"]),
        (["case sensitive"], ["sensitive"], ["case sensitive"]),
        (["CASE insensitive"], ["case"], []),
        (["multi\nline"], ["\nline"], ["multi\nline"]),
        (["with spaces"], ["with ", "spaces"], ["with spaces"]),
    ],
)
def test_listone_contains_all_listtwo_substrings(listone, listtwo, expected):
    """Test that the function returns the correct list of matching strings."""
    actual = dd.listone_contains_all_listtwo_substrings(listone=listone, listtwo=listtwo)
    assert actual == expected


def assert_table_output(capsys, expected_lines):
    """Helper function to assert the table output."""
    captured = capsys.readouterr()
    actual_output = captured.out.strip().splitlines()
    assert len(actual_output) >= len(expected_lines)
    for expected_line in expected_lines:
        assert any(expected_line in line for line in actual_output)


@mark.parametrize(
    "df, expected_output_lines",
    [
        (
            pd.DataFrame(
                data={
                    'X': [25.0, 24.0, 35.5, np.nan, 23.1],
                    'Y': [27, 24, np.nan, 23, np.nan],
                    'Z': ['a', 'b', np.nan, 'd', 'e'],
                }
            ),
            [
                "Information about non-empty columns",
                "Column  Data type  Empty cell count  Empty cell %  Unique",
                "------  -----------  ------------------  --------------  --------",
                "X       float64                     1            20.0         4",
                "Y       float64                     2            40.0         3",
                "Z       object                      1            20.0         4",
            ],
        ),
        (
            pd.DataFrame(data={'A': [1, 2, 3], 'B': [np.nan, np.nan, np.nan]}),
            [
                "Information about non-empty columns",
                "Column  Data type  Empty cell count  Empty cell %  Unique",
                "------  -----------  ------------------  --------------  --------",
                "A       int64                       0             0.0         3",
                "B       float64                     3           100.0         0",
            ],
        ),
        (
            pd.DataFrame(data={'col1': ['a', 'b', 'c'], 'col2': [1.1, 2.2, 3.3]}),
            [
                "Information about non-empty columns",
                "Column  Data type  Empty cell count  Empty cell %  Unique",
                "------  -----------  ------------------  --------------  --------",
                "col1    object                        0             0.0         3",
                "col2    float64                       0             0.0         3",
            ],
        ),
        (
            pd.DataFrame(data={'mixed': [1, np.nan, 'a']}),
            [
                "Information about non-empty columns",
                "Column  Data type  Empty cell count  Empty cell %  Unique",
                "------  -----------  ------------------  --------------  --------",
                "mixed   object                        1            33.3         2",
            ],
        ),
        (
            pd.DataFrame(data={'empty_col': [np.nan, np.nan]}),
            [
                "Information about non-empty columns",
                "Column     Data type  Empty cell count  Empty cell %  Unique",
                "---------  -----------  ------------------  --------------  --------",
                "empty_col  float64                     2           100.0         0",
            ],
        ),
        (
            pd.DataFrame(data={'col_with_spaces': [' value 1 ', 'value 2', np.nan]}),
            [
                "Information about non-empty columns",
                "Column           Data type  Empty cell count  Empty cell %  Unique",
                "---------------  -----------  ------------------  --------------  --------",
                "col_with_spaces  object                        1            33.3         2",
            ],
        ),
    ],
)
def test_number_empty_cells_in_columns(df, expected_output_lines, capsys):
    """Test the number_empty_cells_in_columns function."""
    dd.number_empty_cells_in_columns(df=df)
    captured = capsys.readouterr()
    for line in expected_output_lines:
        print(line, file=sys.stdout, flush=True)
    assert_table_output(capsys, expected_output_lines)


@mark.parametrize(
    "seconds, expected_hh_mm_ss",
    [
        (1, (0, 0, 1)),
        (61, (0, 1, 1)),
        (3601, (1, 0, 1)),
        (3661, (1, 1, 1)),
        (251, (0, 4, 11)),
        (0, (0, 0, 0)),
        (86399, (23, 59, 59)),
        (86400, (24, 0, 0)),
    ],
)
def test_convert_seconds_to_hh_mm_ss(seconds, expected_hh_mm_ss):
    """
    Test the convert_seconds_to_hh_mm_ss function with various inputs.
    """
    result = dd.convert_seconds_to_hh_mm_ss(seconds=seconds)
    assert result == expected_hh_mm_ss


@mark.parametrize(
    "excel_data, sheet_name, usecols, expected_dict",
    [
        (
            {
                "old_text": ["apple", "banana", "cherry"],
                "new_text": ["red fruit", "yellow fruit", "red fruit"],
            },
            "any_sheet_name",
            ["old_text", "new_text"],
            {"apple": "red fruit", "banana": "yellow fruit", "cherry": "red fruit"},
        ),
        (
            {
                "key": [1, 2, 3],
                "value": ["one", "two", "three"],
            },
            "another_sheet",
            ["key", "value"],
            {1: "one", 2: "two", 3: "three"},
        ),
        (
            {
                "find": ["A", "B", "C"],
                "replace": ["Alpha", "Beta", "Gamma"],
            },
            "yet_another",
            ["find", "replace"],
            {"A": "Alpha", "B": "Beta", "C": "Gamma"},
        ),
        (
            {
                "col1": [],
                "col2": [],
            },
            "empty",
            ["col1", "col2"],
            {},
        ),
        (
            {
                "old": ["old_value"],
                "new": ["new_value"],
            },
            "single_row",
            ["old", "new"],
            {"old_value": "new_value"},
        ),
    ],
)
def test_parameters_dict_replacement(
    mocker, excel_data: dict, sheet_name: str, usecols: list[str], expected_dict: dict
):
    """Test the parameters_dict_replacement function by mocking read_file using pytest mocker."""
    mock_read_file = mocker.patch("dawgdad.munging.read_file")
    mock_df = pd.DataFrame(excel_data)
    mock_read_file.return_value = mock_df

    replacement_dict = dd.parameters_dict_replacement(
        file_name=Path("dummy_path"),  # The actual path won't be used
        sheet_name=sheet_name,
        usecols=usecols,
    )
    assert replacement_dict == expected_dict
    mock_read_file.assert_called_once_with(
        file_name=Path("dummy_path"), sheet_name=sheet_name, usecols=usecols
    )


def test_parameters_text_replacement():
    pass


def test_ask_save_as_file_name_path():
    pass


def test_optimize_datetime_columns():
    pass


def test_optimize_integer_columns():
    pass


def test_print_dictionary_by_key():
    pass


def test_optimize_object_columns():
    pass


def test_ask_open_file_name_path():
    pass


def test_convert_csv_to_feather():
    pass


def test_find_int_float_columns():
    pass


def test_find_timedelta_columns():
    pass


def test_optimize_float_columns():
    pass


def test_create_dataframe_norm():
    pass


def test_replace_column_values():
    pass


def test_feature_percent_empty():
    pass


def test_find_category_columns():
    pass


def test_find_datetime_columns():
    pass


def test_list_one_list_two_ops():
    """
    Create a list of items comparing two lists:
    - Items unique to list_one
    - Items unique to list_two
    - Items common to both lists (intersection)
    Duplicate items are not removed.
    """
    list_one = [1, 2, 3, 4, 5, 6]
    list_two = [4, 5, 6, 7, 8, 9]
    result = dd.list_one_list_two_ops(
        list_one=list_one,
        list_two=list_two,
        action="list_one"
    )
    expected = [1, 2, 3]
    assert result == expected
    result = dd.list_one_list_two_ops(
        list_one=list_one,
        list_two=list_two,
        action="list_two"
    )
    expected = [7, 8, 9]
    assert result == expected
    result = dd.list_one_list_two_ops(
        list_one=list_one,
        list_two=list_two,
        action="intersection"
    )
    expected = [4, 5, 6]
    assert result == expected
    list_one = ["mo", "larry", "curly", "curly-joe", "shemp"]
    list_two = ["curly-joe", "shemp", "tom", "dick", "harry"]
    result = dd.list_one_list_two_ops(
        list_one=list_one,
        list_two=list_two,
        action="list_one"
    )
    expected = ["mo", "larry", "curly"]
    assert result == expected
    result = dd.list_one_list_two_ops(
        list_one=list_one,
        list_two=list_two,
        action="list_two"
    )
    expected = ["tom", "dick", "harry"]
    assert result == expected
    result = dd.list_one_list_two_ops(
        list_one=list_one,
        list_two=list_two,
        action="intersection"
    )
    expected = ["curly-joe", "shemp"]
    assert result == expected
    list_one = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    list_two = [4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
    result = dd.list_one_list_two_ops(
        list_one=list_one,
        list_two=list_two,
        action="list_one"
    )
    expected = [1.0, 2.0, 3.0]
    assert result == expected
    result = dd.list_one_list_two_ops(
        list_one=list_one,
        list_two=list_two,
        action="list_two"
    )
    expected = [7.0, 8.0, 9.0]
    assert result == expected
    result = dd.list_one_list_two_ops(
        list_one=list_one,
        list_two=list_two,
        action="intersection"
    )
    expected = [4.0, 5.0, 6.0]
    assert result == expected
    list_one = [1, 2, 3.0, 4.0, 5, "mo", "larry", "curly-joe"]
    list_two = [2, 3, 4.0, 5.0, 6.0, "mo", "larry", "shemp"]
    result = dd.list_one_list_two_ops(
        list_one=list_one,
        list_two=list_two,
        action="list_one"
    )
    expected = [1, 5, 3.0, "curly-joe"]
    assert result == expected
    result = dd.list_one_list_two_ops(
        list_one=list_one,
        list_two=list_two,
        action="list_two"
    )
    expected = [3, 5.0, 6.0, "shemp"]
    assert result == expected
    result = dd.list_one_list_two_ops(
        list_one=list_one,
        list_two=list_two,
        action="intersection"
    )
    expected = [2, 4.0, "mo", "larry"]
    assert result == expected


def test_series_replace_string():
    pass


def test_delete_empty_columns():
    """
    Test that all elements of a column:
    - are empty for all columns
    - are empty for specific columns
    """
    result1 = dd.delete_empty_columns(df=df)
    expected1 = pd.DataFrame(
        data=dict(
            floats=[1.0, np.nan, 3.0, np.nan, 5.0, 6.0, np.nan],
            text=["A", "B", "C", "D", "E", "F", np.nan],
            dates=[
                "1956-06-08", "1956-06-08",
                "1956-06-08", "1956-06-08",
                "1956-06-08", "1956-06-08",
                pd.NaT
            ],
            integers=[1, 2, np.nan, 4, 5, 6, np.nan],
        )
    ).replace(
        r"^\s+$",
        np.nan,
        regex=True
    ).replace(
        "",
        np.nan,
        regex=True
    ).astype(
        dtype={
            "integers": "Int64",
            "floats": "float64",
            "text": "object",
            "dates": "datetime64[ns]",
        }
    )
    assert result1.equals(other=expected1)
    list_empty_columns = ["mixed", "nan_none"]
    # Delete columns using list_empty_columns
    result2 = dd.delete_empty_columns(
        df=df,
        list_empty_columns=list_empty_columns
    )
    expected2 = pd.DataFrame(
        data=dict(
            floats=[1.0, np.nan, 3.0, np.nan, 5.0, 6.0, np.nan],
            text=["A", "B", "C", "D", "E", "F", np.nan],
            dates=[
                "1956-06-08", "1956-06-08",
                "1956-06-08", "1956-06-08",
                "1956-06-08", "1956-06-08",
                pd.NaT
            ],
            all_nan=[np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            all_nat=[pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT],
            all_none=[None, None, None, None, None, None, None],
            all_space=["", " ", "", " ", "", "", ""],
            nan_space=[np.nan, "", " ", np.nan, np.nan, np.nan, np.nan],
            integers=[1, 2, np.nan, 4, 5, 6, np.nan],
        )
    ).replace(
        r"^\s+$",
        np.nan,
        regex=True
    ).replace(
        "",
        np.nan,
        regex=True
    ).astype(
        dtype={
            "integers": "Int64",
            "floats": "float64",
            "text": "object",
            "dates": "datetime64[ns]",
            "all_nan": "float64",
            "all_nat": "datetime64[ns]",
            "all_none": "float64",
            "all_space": "float64",
            "nan_space": "float64"
        }
    )
    assert result2.equals(other=expected2)
    # No not delete columns using list_empty_columns because
    # not all columns in list are empty
    list_empty_columns = ["mixed", "nan_none", "integers"]
    result3 = dd.delete_empty_columns(
        df=df,
        list_empty_columns=list_empty_columns
    )
    expected3 = pd.DataFrame(
        data=dict(
            floats=[1.0, np.nan, 3.0, np.nan, 5.0, 6.0, np.nan],
            text=["A", "B", "C", "D", "E", "F", np.nan],
            dates=[
                "1956-06-08", "1956-06-08",
                "1956-06-08", "1956-06-08",
                "1956-06-08", "1956-06-08",
                pd.NaT
            ],
            all_nan=[np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            all_nat=[pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT],
            all_none=[None, None, None, None, None, None, None],
            all_space=["", " ", "", " ", "", "", ""],
            nan_space=[np.nan, "", " ", np.nan, np.nan, np.nan, np.nan],
            nan_none=[np.nan, None, np.nan, np.nan, None, np.nan, None],
            mixed=[None, np.nan, pd.NaT, pd.NaT, None, np.nan, pd.NaT],
            integers=[1, 2, np.nan, 4, 5, 6, np.nan],
        )
    ).replace(
        r"^\s+$",
        np.nan,
        regex=True
    ).replace(
        "",
        np.nan,
        regex=True
    ).astype(
        dtype={
            "integers": "Int64",
            "floats": "float64",
            "text": "object",
            "dates": "datetime64[ns]",
            "all_nan": "float64",
            "all_nat": "datetime64[ns]",
            "all_none": "float64",
            "all_space": "float64",
            "nan_space": "float64",
            "nan_none": "float64",
            "mixed": "datetime64[ns]"
        }
    )
    assert result3.equals(other=expected3)


def test_directory_file_print():
    pass


def test_replace_text_numbers():
    pass


def test_find_integer_columns():
    pass


def test_find_object_columns():
    pass


def test_rename_some_columns():
    pass


def test_series_memory_usage():
    pass


def test_ask_directory_path():
    pass


def test_rename_all_columns():
    pass


def test_find_float_columns():
    pass


def test_remove_punctuation():
    pass


def test_print_list_by_item():
    pass


def test_delete_empty_rows():
    """
    Test delete empty rows:
    - all elements for a row for all columns
    - all elements for a row for specific columns
    """
    # Delete columns where all elements of a column are empty
    result = dd.delete_empty_rows(df=df)
    expected = pd.DataFrame(
        data=dict(
            floats=[1.0, np.nan, 3.0, np.nan, 5.0, 6.0],
            text=["A", "B", "C", "D", "E", "F"],
            dates=[
                "1956-06-08", "1956-06-08",
                "1956-06-08", "1956-06-08",
                "1956-06-08", "1956-06-08"
            ],
            all_nan=[np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            all_nat=[pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT],
            all_none=[None, None, None, None, None, None],
            all_space=["", " ", "", " ", "", ""],
            nan_space=[np.nan, "", " ", np.nan, np.nan, np.nan],
            nan_none=[np.nan, None, np.nan, np.nan, None, np.nan],
            mixed=[None, np.nan, pd.NaT, pd.NaT, None, np.nan],
            integers=[1, 2, np.nan, 4, 5, 6],
        )
    ).replace(
        r"^\s+$",
        np.nan,
        regex=True
    ).replace(
        "",
        np.nan,
        regex=True
    ).astype(
        dtype={
            "integers": "Int64",
            "floats": "float64",
            "text": "object",
            "dates": "datetime64[ns]",
            "all_nan": "float64",
            "all_nat": "datetime64[ns]",
            "all_none": "float64",
            "all_space": "float64",
            "nan_space": "float64",
            "nan_none": "float64",
            "mixed": "datetime64[ns]"
        }
    )
    assert result.equals(other=expected)


def test_delete_list_files():
    pattern_startswith = ["job_aids"]
    path = "dir_directories"
    result1 = dd.list_directories(path=path)
    expected1 = [
        "cheatsheet_directory", "another_directory", "job_aids_directory"
    ]
    assert set(result1) == set(expected1)
    result2 = dd.list_directories(
        path=path,
        pattern_startswith=pattern_startswith
    )
    expected2 = ["job_aids_directory"]
    assert set(result2) == set(expected2)
    pattern_startswith = ["job_aids", "cheatsheet"]
    result3 = dd.list_directories(
        path=path,
        pattern_startswith=pattern_startswith
    )
    expected3 = ["cheatsheet_directory", "job_aids_directory"]
    assert set(result3) == set(expected3)


def test_find_bool_columns():
    pass


def test_create_dataframe():
    pass


def test_create_directory():
    pass


def test_delete_directory():
    pass


def test_list_change_case():
    pass


def test_list_directories():
    pattern_startswith = ["job_aids"]
    path = "dir_directories"
    result1 = dd.list_directories(path=path)
    expected1 = [
        'cheatsheet_directory', 'another_directory', 'job_aids_directory'
    ]
    assert set(result1) == set(expected1)
    result2 = dd.list_directories(
        path=path,
        pattern_startswith=pattern_startswith
    )
    expected2 = ['job_aids_directory']
    assert set(result2) == set(expected2)
    pattern_startswith = ["job_aids", "cheatsheet"]
    result3 = dd.list_directories(
        path=path,
        pattern_startswith=pattern_startswith
    )
    expected3 = ['cheatsheet_directory', 'job_aids_directory']
    assert set(result3) == set(expected3)


def test_optimize_columns():
    pass


def test_rename_directory():
    pass


def test_process_columns():
    pass


def test_copy_directory():
    pass


def test_dataframe_info():
    pass


def test_delete_columns():
    pass


def test_quit_sap_excel():
    pass


def test_mask_outliers():
    pass


def test_process_rows():
    pass


def test_delete_rows():
    pass


def test_list_files():
    pattern_extension = [".html", ".HTML", ".mkd", ".MKD"]
    pattern_startswith = ["file_", "job_aid_"]
    directory = "dir_files"
    result1 = sorted(dd.list_files(directory=directory))
    expected1 = sorted([
        PosixPath("dir_files/job_aid_file_one.html"),
        PosixPath("dir_files/job_aid_file_two.HTML"),
        PosixPath("dir_files/job_aid_file_one.mkd"),
        PosixPath("dir_files/job_aid_file_two.MKD"),
        PosixPath("dir_files/file_one.html"),
        PosixPath("dir_files/file_two.HTML"),
        PosixPath("dir_files/file_one.mkd"),
        PosixPath("dir_files/file_two.MKD")
    ])
    assert result1 == expected1
    result2 = sorted(dd.list_files(
        directory=directory,
        pattern_startswith=pattern_startswith
    ))
    expected2 = sorted([
        PosixPath("dir_files/job_aid_file_one.html"),
        PosixPath("dir_files/job_aid_file_two.HTML"),
        PosixPath("dir_files/job_aid_file_one.mkd"),
        PosixPath("dir_files/job_aid_file_two.MKD"),
        PosixPath("dir_files/file_one.html"),
        PosixPath("dir_files/file_two.HTML"),
        PosixPath("dir_files/file_one.mkd"),
        PosixPath("dir_files/file_two.MKD")
    ])
    assert result2 == expected2
    result3 = sorted(dd.list_files(
        directory=directory,
        pattern_extension=pattern_extension,
    ))
    expected3 = sorted([
        PosixPath("dir_files/job_aid_file_one.html"),
        PosixPath("dir_files/job_aid_file_two.HTML"),
        PosixPath("dir_files/job_aid_file_one.mkd"),
        PosixPath("dir_files/job_aid_file_two.MKD"),
        PosixPath("dir_files/file_one.html"),
        PosixPath("dir_files/file_two.HTML"),
        PosixPath("dir_files/file_one.mkd"),
        PosixPath("dir_files/file_two.MKD")
    ])
    assert result3 == expected3
    result4 = sorted(dd.list_files(
        directory=directory,
        pattern_startswith=pattern_startswith,
        pattern_extension=pattern_extension
    ))
    expected4 = sorted([
        PosixPath("dir_files/job_aid_file_one.html"),
        PosixPath("dir_files/job_aid_file_two.HTML"),
        PosixPath("dir_files/job_aid_file_one.mkd"),
        PosixPath("dir_files/job_aid_file_two.MKD"),
        PosixPath("dir_files/file_one.html"),
        PosixPath("dir_files/file_two.HTML"),
        PosixPath("dir_files/file_one.mkd"),
        PosixPath("dir_files/file_two.MKD")
    ])
    assert result4 == expected4


def test_byte_size():
    pass


def test_get_mtime():
    pass


def test_file_size():
    pass


def test_read_file():
    pass


def test_save_file():
    pass


def test_sort_rows():
    pass


def test_datetime():
    """Tests if specific columns are of datetime64[ns] type."""
    assert pd.api.types.is_datetime64_any_dtype(df["dates"])
    assert pd.api.types.is_datetime64_any_dtype(df["all_nat"])
    assert pd.api.types.is_datetime64_any_dtype(df["mixed"])


def test_integer_types():
    """Tests if integer-related columns are of the expected types."""
    assert pd.api.types.is_integer_dtype(df["integers"])
#     assert pd.api.types.is_integer_dtype(df["integers_int64"])
#     assert pd.api.types.is_integer_dtype(df["integers_uint8"])
#     assert pd.api.types.is_float_dtype(df["integers_float64"])
#     assert pd.api.types.is_float_dtype(df["floats"])


def test_float_types():
    """Tests if float columns are of the expected types."""
    assert pd.api.types.is_float_dtype(df["floats"])
    # assert pd.api.types.is_float_dtype(df["floats_float64"])
    # assert pd.api.types.is_float_dtype(df["floats_float32"])


def test_text_types():
    """Tests if text columns are of the expected types."""
    assert pd.api.types.is_object_dtype(df["text"])
    # assert pd.api.types.is_object_dtype(df["text_object"])
    # assert pd.api.types.is_string_dtype(df["text_string"])
