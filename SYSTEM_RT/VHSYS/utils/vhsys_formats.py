    def format_datetime(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(value, str):
        if len(value) == 10:
            value += " 00:00:00"
        try:
            date_object = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return date_object.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            # trunk-ignore(ruff/B904)
            raise ValueError(
                "The input value is not a valid datetime or string representation of a datetime."
            )
    elif value is not None:
        raise ValueError(
            "The input value is not a valid datetime or string representation of a datetime."
        )
    else:
        return None
