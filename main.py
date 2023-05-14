from openapi.parser import OpenAPIParser
from openapi.validator import Validator
from openapi.rule_generator import RuleGenerator
from openapi.enhancer import Enhancer
from embeddings.fasttext_model import FastTextTrainer


def main():
    model_path = "rest_model"
    fasttext_trainer = FastTextTrainer("APIs-guru/specifications", model_path)
    fasttext_trainer.load_model(model_path)

    rule_generator = RuleGenerator("settings2.yaml", fasttext_trainer)

    spec_parser = OpenAPIParser('benchmark/swagger/fdic.yaml')
    operations = spec_parser.parse_operations()

    parsed_rules = {}
    for operation in operations:
        print(operation['operation_id'] + " is processing...")
        param_names = [param['name'] for param in operation["parameters"]]
        operation_rules = {}
        for parameter in operation["parameters"]:
            param_rule = rule_generator.extract_keywords(parameter['description'], param_names)
            if param_rule:
                operation_rules[parameter['name']] = rule_generator.extract_keywords(parameter['description'], param_names)
        parsed_rules[operation['operation_id']] = operation_rules

    validator = Validator()
    validated_rules = validator.validate(spec_parser.spec, parsed_rules)
    enhancer = Enhancer(validated_rules)
    enhancer.enhance(spec_parser.spec)


if __name__ == "__main__":
    main()
