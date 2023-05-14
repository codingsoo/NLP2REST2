import requests
import datetime


class Validator:

    def __init__(self):
        self.errors = []

    def validate(self, spec, rules):
        validated_rules = {}
        not_validated_rules = {}
        url = spec['schemes'][0] + '://' + spec['host'] + spec['basePath']
        paths = spec.get('paths')
        for path, methods in paths.items():
            for method, operation in methods.items():
                if operation.get('operationId') in rules:
                    operation_rules = rules[operation.get('operationId')]
                    for param in operation['parameters']:
                        if param['name'] in operation_rules:
                            validated_param_rules = {}
                            not_validated_param_rules = {}
                            for rule, value in operation_rules[param['name']].items():
                                result = self.static_validation(rule, value, param)
                                if result is None:
                                    not_validated_param_rules[rule] = {
                                        'value': value,
                                        'method': method,
                                        'url': url + path,
                                        'required_params': {p['name']: p['default'] for p in operation['parameters'] if
                                                            p['required']},
                                        'param': param
                                    }
                                elif result:
                                    validated_param_rules[rule] = value
                            if validated_param_rules:
                                if operation.get('operationId') not in validated_rules:
                                    validated_rules[operation.get('operationId')] = {}
                                validated_rules[operation.get('operationId')][param['name']] = validated_param_rules
                            if not_validated_param_rules:
                                if operation.get('operationId') not in not_validated_rules:
                                    not_validated_rules[operation.get('operationId')] = {}
                                not_validated_rules[operation.get('operationId')][param['name']] = not_validated_param_rules
        # Apply dynamic validation for the rules that need it
        for operationId, params in not_validated_rules.items():
            for paramName, paramRules in params.items():
                for rule, rule_info in paramRules.items():
                    result = self.dynamic_validation(rule, rule_info['value'], rule_info['param'], rule_info['method'],
                                                     rule_info['url'], rule_info['required_params'])
                    if result:
                        if operationId not in validated_rules:
                            validated_rules[operationId] = {}
                        if paramName not in validated_rules[operationId]:
                            validated_rules[operationId][paramName] = {}
                        if isinstance(result, list):
                            validated_rules[operationId][paramName][rule] = result
                        else:
                            validated_rules[operationId][paramName][rule] = rule_info['value']
        return validated_rules

    def dynamic_validation(self, rule, value, parameter, method, url, required_params):
        if rule == "example":
            validated_values = []
            for example_value in value:
                if self._validate_single_value(example_value, parameter, method, url, required_params):
                    validated_values.append(example_value)
            return validated_values
        elif rule == "maximum":
            # Check if value is a number
            if isinstance(value, (int, float)):
                # Validate the maximum value
                if not self._validate_single_value(value, parameter, method, url, required_params):
                    return False

                # Validate the maximum value + 1
                if self._validate_single_value(value + 1, parameter, method, url, required_params):
                    return False

                # If both checks pass, return True
                return True
            else:
                self.errors.append(f"Rule {rule} with value {value} for parameter {parameter['name']} is not a number.")
                return False
        elif rule == "minimum":
            # Check if value is a number
            if isinstance(value, (int, float)):
                # Validate the minimum value
                if not self._validate_single_value(value, parameter, method, url, required_params):
                    return False

                # Validate the minimum value - 1
                if self._validate_single_value(value - 1, parameter, method, url, required_params):
                    return True

                # If both checks pass, return True
                return True
            else:
                self.errors.append(f"Rule {rule} with value {value} for parameter {parameter['name']} is not a number.")
                return False
        elif rule == "type" and value == "number":
            # Send a number (1.1) for validation
            if self._validate_single_value(1.1, parameter, method, url, required_params):
                return True
            else:
                return False
        elif rule == "default":
            # Send request without the default value
            no_default_response = requests.request(method, url, params=required_params)

            # Send request with the default value
            request_params = {**required_params, parameter['name']: value}
            default_response = requests.request(method, url, params=request_params)

            # Compare responses
            if no_default_response.status_code == default_response.status_code and no_default_response.text == default_response.text:
                return True
            else:
                self.errors.append(
                    f"Rule {rule} with value {value} for parameter {parameter['name']} does not match the response when no value is provided.")
                return False
        elif rule == "minMax":
            if not self._validate_single_value(value[0], parameter, method, url, required_params):
                return False

            # Validate the maximum value
            if not self._validate_single_value(value[1], parameter, method, url, required_params):
                return False

            # Validate the minimum value - 1
            if self._validate_single_value(value[0] - 1, parameter, method, url, required_params):
                return False

            # Validate the maximum value + 1
            if self._validate_single_value(value[1] + 1, parameter, method, url, required_params):
                return False

            # If all checks pass, return True
            return True
        else:
            return self._validate_single_value(value, parameter, method, url, required_params)

    def _validate_single_value(self, value, parameter, method, url, required_params):
        try:
            if not self.is_successful_request(method, url, required_params):
                self.errors.append(f"Required parameters for operation could not generate a successful request.")
                return False

            request_params = {**required_params, parameter['name']: value}
            response = requests.request(method, url, params=request_params)
            if 200 <= response.status_code < 300:
                return True
            else:
                return False
        except requests.exceptions.RequestException as e:
            self.errors.append(f"Request to {url} failed: {e}")
            return False

    def is_successful_request(self, method, url, params):
        try:
            response = requests.request(method, url, params=params)
            return 200 <= response.status_code < 300
        except requests.exceptions.RequestException as e:
            self.errors.append(f"Request to {url} failed: {e}")
            return False

    def static_validation(self, rule, value, parameter):
        if rule == "collectionFormat":
            if value == "csv":
                example = parameter.get('x-example') or parameter.get('example')
                if example:
                    if ',' in example:
                        return True
                    else:
                        return False
        elif rule == "type":
            example = parameter.get('x-example') or parameter.get('example')
            if example:
                if value == "array":
                    if ',' in example:
                        return True
                    else:
                        return False
                elif value == "object":
                    if '{' in example and '}' in example:
                        return True
                    else:
                        return False
        elif rule == "format":
            example = parameter.get('x-example') or parameter.get('example')

            if example:
                if value == "date":
                    try:
                        datetime.datetime.strptime(example, '%Y-%m-%d')  # try to parse as date
                        return True
                    except Exception:
                        return False
                elif value == "date-time":
                    try:
                        datetime.datetime.strptime(example, '%Y-%m-%dT%H:%M:%S')  # try to parse as datetime
                        return True
                    except Exception:
                        return False
                elif value == "hostname":
                    if 'http' in example:
                        return True
                    else:
                        return False
        elif rule in ["default", "minimum", "maximum", "type"]:
            if parameter.get(rule) == value:
                return True
        return None

    def get_errors(self):
        return self.errors
