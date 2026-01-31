def options_to_str(options: dict | None = None) -> str:
    if not options:
        return ''

    option_items = []
    for key, value in options.items():
        if value is not None:
            fixed_value = str(value).lower() if isinstance(value, bool) else value
            option_items.append(f'{key} {fixed_value}')

    return f' ({", ".join(option_items)})'
