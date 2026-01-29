from croniter import croniter


def compress_field(values: list) -> str:
    """
    Compresses a list of integer values from an expanded cron field
    into a cron-standard string (e.g., [1, 2, 3, 5] -> '1-3,5').
    """
    if not values or not all(isinstance(v, int) for v in values):
        # Handle special non-integer values like ['*'] or ['l']
        return str(values[0])

    sorted_values = sorted(list(set(values)))

    compressed_parts = []
    i = 0
    while i < len(sorted_values):
        start = sorted_values[i]
        j = i
        # Find the end of a consecutive sequence
        while (
            j + 1 < len(sorted_values) and sorted_values[j + 1] == sorted_values[j] + 1
        ):
            j += 1

        end = sorted_values[j]

        # If the sequence has 3 or more numbers, use a dash (e.g., 1-3)
        if end > start + 1:
            compressed_parts.append(f"{start}-{end}")
        # Otherwise, list each number individually
        else:
            for k in range(start, end + 1):
                compressed_parts.append(str(k))

        i = j + 1

    return ",".join(compressed_parts)


def normalize_cron(expression: str) -> str:
    """
    Takes a cron expression string and returns a deterministic,
    normalized version of it.

    This is useful for comparing two expressions for equality, ignoring
    superficial differences like extra spaces or using lists vs. ranges.
    """
    try:
        # Step 1: Expand the cron expression into its component parts
        expanded_list, nth_map = croniter.expand(expression)
    except Exception as e:
        raise ValueError(f"Invalid cron expression: '{expression}'") from e

    final_parts = []

    # Step 2: Iterate through each field and compress it back to a string
    for i, field_values in enumerate(expanded_list):
        # The 5th field (index 4) is day-of-week and needs special handling
        # for the 'nth weekday' syntax (e.g., 2#3)
        if i == 4 and nth_map:
            dow_parts = []
            # Sort for deterministic output
            for day, occurrences in sorted(nth_map.items()):
                for n in sorted(list(occurrences)):
                    dow_parts.append(f"{day}#{n}")
            final_parts.append(",".join(dow_parts))
        else:
            # For all other fields, use the standard compression logic
            final_parts.append(compress_field(field_values))

    # Step 3: Join the parts with single spaces for the final string
    return " ".join(final_parts)
