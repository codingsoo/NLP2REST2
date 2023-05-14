import json

class Enhancer:
    def __init__(self, validated_rules):
        self.validated_rules = validated_rules

    def enhance(self, spec):
        enhanced_spec = spec.copy()
        paths = enhanced_spec.get('paths')
        for path, methods in paths.items():
            for method, operation in methods.items():
                if operation.get('operationId') in self.validated_rules:
                    operation_rules = self.validated_rules[operation.get('operationId')]
                    for param in operation['parameters']:
                        if param['name'] in operation_rules:
                            for rule, value in operation_rules[param['name']].items():
                                if value == "array":
                                    param["items"] = {}
                                    param["items"]["type"] = param["type"]

                                if rule == "example":
                                    param["x-examples"] = value
                                else:
                                    param[rule] = value
        with open('output.json', 'w') as f:
            json.dump(enhanced_spec, f, indent=4)
