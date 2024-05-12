from random import randint
from math import floor
from random import uniform, choice
from typing import *

from static.dependencies.exceptions import Exceptions


output_dict = {'success': False, 'errorMessage': str(), 'response': dict()}

class Randomizer:
    @staticmethod
    def int_number(min_value: Any, max_value: Any) -> dict:
        # Input parameter validation
        if not str(min_value).strip() or not str(max_value).strip():
            output_dict['errorMessage'] = Exceptions.EMPTY_PARAMETERS_VALUE.message.format('min_value, max_value')
            return output_dict

        try:
            min_value, max_value = int(min_value), int(max_value)
        except ValueError:
            parameter_name = 'min_value' if not isinstance(min_value, int) else 'max_value'
            output_dict['errorMessage'] = Exceptions.INVALID_PARAMETER_VALUE.message.format(parameter_name, 'integer')
            return output_dict

        if min_value >= max_value:
            output_dict['errorMessage'] = Exceptions.PARAMETER_MUST_BE_LESS_THAN.message.format('min_value', 'max_value')
            return output_dict

        #  Main process
        generated_number = int(randint(min_value, max_value))
        output_data = {'number': generated_number}
        output_dict['success'], output_dict['response'] = True, output_data

        return output_dict

    @staticmethod
    def float_number(min_value: Any, max_value: Any) -> dict:
        # Input parameter validation
        if not str(min_value).strip() or not str(max_value).strip():
            output_dict['errorMessage'] = Exceptions.EMPTY_PARAMETERS_VALUE.message.format('min_value, max_value')
            return output_dict

        try:
            min_value, max_value = float(min_value), float(max_value)
        except ValueError:
            parameter_name = 'min_value' if not isinstance(min_value, float) else 'max_value'
            output_dict['errorMessage'] = Exceptions.INVALID_PARAMETER_VALUE.message.format(parameter_name, 'float')
            return output_dict

        if min_value >= max_value:
            output_dict['errorMessage'] = Exceptions.PARAMETER_MUST_BE_LESS_THAN.message.format('min_value', 'max_value')
            return output_dict

        min_value_mantisse = str(min_value).split('.', 1)[1]
        max_value_mantisse = str(max_value).split('.', 1)[1]

        if min_value_mantisse == '0' and max_value_mantisse == '0':
            output_precision = 1
        else:
            smallest_mantisse = min(len(min_value_mantisse), len(max_value_mantisse))
            largest_mantisse = max(len(min_value_mantisse), len(max_value_mantisse))
            output_precision = choice(range(smallest_mantisse, largest_mantisse + 1))

        generated_number = float(uniform(min_value, max_value))
        output_data = {'number': round(floor(generated_number * 10 ** output_precision) / 10 ** output_precision, output_precision)}
        output_dict['success'], output_dict['response'] = True, output_data

        return output_dict
