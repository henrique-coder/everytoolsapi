from typing import Any, Union
from time import perf_counter


def main(request_data: Any) -> Union[dict, None]:
    start_time = perf_counter()
    generated_data = dict()

    if not request_data:
        return None

    try:
        generated_data['data'] = str(request_data.remote_addr)
    except BaseException:
        return None

    generated_data['processing_time'] = float(perf_counter() - start_time)

    return generated_data
