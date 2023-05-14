from prance import ResolvingParser


def load_spec(spec_file):
    """
    Loads an OpenAPI specification from a given file.

    Parameters:
    spec_file (str): The path to the OpenAPI specification file.

    Returns:
    dict: The parsed OpenAPI specification.
    """
    # Load OpenAPI specification from file
    parser = ResolvingParser(spec_file)
    return parser.specification


class OpenAPIParser:
    """
    A parser for OpenAPI specifications. The parser loads a specification and extracts its operations.

    Attributes:
    spec (dict): The loaded OpenAPI specification.
    version (int): The version of the OpenAPI specification (2 or 3).
    operations (list): The operations extracted from the specification.
    """

    def __init__(self, spec_file):
        """
        Initializes the parser and loads an OpenAPI specification from a file.

        Parameters:
        spec_file (str): The path to the OpenAPI specification file.
        """
        self.spec = load_spec(spec_file)
        if "swagger" in self.spec:
            self.version = 2
        else:
            self.version = 3

        self.operations = self.parse_operations()

    def parse_operations(self):
        """
        Parses the loaded OpenAPI specification and extracts its operations.

        Returns:
        list: A list of operations, each represented as a dictionary with the keys 'path', 'method', 'operation_id',
        'description', 'summary', and 'parameters'.
        """
        # Parse OpenAPI specification and extract operations
        operations = []
        paths = self.spec.get('paths', {})
        for path, methods in paths.items():
            for method, operation in methods.items():
                if method in ['get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace']:
                    parameters = operation.get('parameters', [])
                    parsed_operation = {
                        'path': path,
                        'method': method,
                        'operation_id': operation.get('operationId'),
                        'description': operation.get('description'),
                        'summary': operation.get('summary'),
                        'parameters': parameters
                    }
                    operations.append(parsed_operation)
        return operations
