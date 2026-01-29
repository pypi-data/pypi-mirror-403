import re

def concatenate_strings(separator, *args):
    # Filter out None values and join the non-None strings
    non_none_args = [arg for arg in args if arg is not None]
    result = separator.join(non_none_args)

    return result


def remove_duplications(string):
    # Split the string using both "," and ";" as delimiters
    parts = re.split(r'[;,]', string)

    # Remove duplicates by converting the list to a set
    unique_parts = set([s.strip() for s in parts])

    # Initialize a list to store the sub-elements
    sub_elements = list(unique_parts)

    # Join the sub-elements back together
    result = ', '.join(sub_elements)

    return result

