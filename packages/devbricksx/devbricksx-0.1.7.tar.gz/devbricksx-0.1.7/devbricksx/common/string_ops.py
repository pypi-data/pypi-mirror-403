TRIMMED_LENGTH = 100
def to_trimmed_str(obj) -> str:
    if obj is None:
        return ""

    str_of_output = str(obj)

    if len(str_of_output) > TRIMMED_LENGTH:
        trimmed_string = str_of_output[:TRIMMED_LENGTH] + "..."  # Adds an ellipsis to indicate truncation
    else:
        trimmed_string = str_of_output

    return trimmed_string
