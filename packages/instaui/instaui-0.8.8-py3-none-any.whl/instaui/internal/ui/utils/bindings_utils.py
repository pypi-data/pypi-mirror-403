from instaui.internal.ui.input_slient_data import InputSilentData
from instaui.internal.ui.bindable import is_bindable


def auto_made_inputs_to_slient(
    inputs: list,
    outputs: list,
):
    if (not inputs) or (not outputs):
        return inputs

    outputs_set = set(outputs)

    return [
        InputSilentData(input) if is_bindable(input) and input in outputs_set else input
        for input in inputs
    ]
