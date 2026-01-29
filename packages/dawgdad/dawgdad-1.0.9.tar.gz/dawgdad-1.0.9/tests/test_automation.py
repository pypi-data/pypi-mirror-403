from pytest import mark

import dawgdad as dd


def test_fahrenheit_to_celsius_table():
    pass


@mark.parametrize(
    "mugs_coffee, cups_tea, mugs_tea, expected_result",
    [
        (0, 0, 0, (0, 0, 0, 0, 0, 0, 0, (0, 0, 0))),
        (0, 0, 1, (300, 0, 0, 0, 300, 0, 0, (0, 1, 42))),
        (0, 1, 0, (400, 0, 0, 400, 0, 0, 0, (0, 2, 16))),
        (0, 1, 1, (700, 0, 0, 400, 300, 0, 0, (0, 3, 58))),
        (1, 0, 0, (370, 220, 150, 0, 0, 225, 20, (0, 2, 5))),
        (1, 0, 1, (670, 220, 150, 0, 300, 225, 20, (0, 3, 47))),
        (1, 1, 0, (770, 220, 150, 400, 0, 225, 20, (0, 4, 21))),
        (1, 1, 1, (1070, 220, 150, 400, 300, 225, 20, (0, 6, 3))),
        (2, 0, 0, (740, 440, 300, 0, 0, 450, 40, (0, 4, 11))),
        (
            2,
            1,
            0,
            (1140, 440, 300, 400, 0, 450, 40, (0, 6, 27)),  # Corrected expected_result
        ),
        (
            0,
            2,
            1,
            (1100, 0, 0, 800, 300, 0, 0, (0, 6, 14)),  # Corrected expected_result
        ),
    ],
)
def test_water_coffee_tea_milk(
    mugs_coffee, cups_tea, mugs_tea, expected_result
):
    """Test the water_coffee_tea_milk function with various inputs."""
    result = dd.water_coffee_tea_milk(
        mugs_coffee=mugs_coffee, cups_tea=cups_tea, mugs_tea=mugs_tea
    )
    assert result == expected_result
