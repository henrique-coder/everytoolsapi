from random import uniform, choice
from typing import Union
from math import floor
from time import perf_counter


def main(min_value: float, max_value: float) -> Union[dict, None]:
    start_time = perf_counter()
    generated_data = dict()

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
        generated_data['data'] = round(floor(generated_number * 10 ** output_precision) / 10 ** output_precision, output_precision)
    except Exception:
        return None

    generated_data['processing_time'] = float(perf_counter() - start_time)

    return generated_data
