from random import randint
from math import floor
from random import uniform, choice
from typing import *

from static.dependencies.functions import APITools
from static.dependencies.exceptions import Exceptions


class Randomizer:
    @staticmethod
    def int_number(input_values: Dict[str, Optional[Any]]) -> dict:
        output_dict = APITools.get_default_output_dict()

        # Input parameter validation
        if not input_values.get('min') or not input_values.get('max'):
            parameter_name = 'min' if not input_values.get('min') else 'max'
            output_dict['errorMessage'] = Exceptions.EMPTY_PARAMETERS_VALUE.message.format(parameter_name)
            return output_dict

        try: min_value, max_value = int(input_values.get('min')), int(input_values.get('max'))
        except ValueError:
            parameter_name = 'min' if not isinstance(input_values.get('min'), int) else 'max'
            output_dict['errorMessage'] = Exceptions.INVALID_PARAMETER_VALUE.message.format(parameter_name, 'integer')
            return output_dict

        if min_value >= max_value:
            output_dict['errorMessage'] = Exceptions.PARAMETER_MUST_BE_LESS_THAN.message.format('min', 'max')
            return output_dict

        #  Main process
        generated_number = int(randint(min_value, max_value))
        output_data = {'number': generated_number}
        output_dict['success'], output_dict['response'] = True, output_data

        return output_dict

    @staticmethod
    def float_number(input_values: Dict[str, Optional[Any]]) -> dict:
        output_dict = APITools.get_default_output_dict()

        # Input parameter validation
        if not input_values.get('min') or not input_values.get('max'):
            parameter_name = 'min' if not input_values.get('min') else 'max'
            output_dict['errorMessage'] = Exceptions.EMPTY_PARAMETERS_VALUE.message.format(parameter_name)
            return output_dict

        try:
            min_value, max_value = float(input_values.get('min')), float(input_values.get('max'))
        except ValueError:
            parameter_name = 'min' if not isinstance(input_values.get('min'), float) else 'max'
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
