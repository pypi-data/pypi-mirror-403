from yta_math_common import Math


# TODO: Maybe we need to indicate if the value
# got clamped or not
def clamp_value_normalized(
    value_normalized: float
) -> float:
    """
    Clamp the `value_normalized` provided, which means
    transforming it into a value that fits in the
    `[0.0, 1.0]` range.
    """
    return (
        1.0
        if value_normalized > 1.0 else
        0.0
        if value_normalized < 0.0 else
        value_normalized
    )

# Common easing function methods below
def smooth(
    t_normalized: float,
    inflection: float = 10.0
):
    error = Math.sigmoid(-inflection / 2)

    return min(
        max((Math.sigmoid(inflection * (t_normalized - 0.5)) - error) / (1 - 2 * error), 0),
        1,
    )