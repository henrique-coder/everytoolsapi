from typing import Union
from time import perf_counter


def main(request_data: str) -> Union[dict, None]:
    start_time = perf_counter()
    generated_data = dict()

    try:
        generated_data['data'] = str(request_data)
    except BaseException:
        return None

    generated_data['processing_time'] = float(perf_counter() - start_time)

    return generated_data
