import ast


def event_dataset_type_adapter(value):
    if value is None:
        return None
    return ast.literal_eval(value)
