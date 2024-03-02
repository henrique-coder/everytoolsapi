from random import uniform, choice
from typing import Union
from math import floor


def main(min_value: float, max_value: float) -> Union[float, None]:
    try:
        min_value_mantisse = str(min_value).split('.', 1)[1]
        max_value_mantisse = str(max_value).split('.', 1)[1]

        if min_value_mantisse == '0' and max_value_mantisse == '0':
            output_precision = 1
        else:
            smallest_mantisse = min(len(min_value_mantisse), len(max_value_mantisse))
            largest_mantisse = max(len(min_value_mantisse), len(max_value_mantisse))
            output_precision = choice(range(smallest_mantisse, largest_mantisse + 1))

        generated_number = uniform(min_value, max_value)
        generated_number = round(floor(generated_number * 10 ** output_precision) / 10 ** output_precision, output_precision)
    except Exception:
        return None

    return generated_number
