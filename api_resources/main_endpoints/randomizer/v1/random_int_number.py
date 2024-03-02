from typing import Union
from random import randint


def main(min_value: int, max_value: int) -> Union[int, None]:
    try:
        generated_number = randint(min_value, max_value)
    except Exception:
        generated_number = None

    return generated_number
