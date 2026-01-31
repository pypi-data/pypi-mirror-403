from datetime import datetime, timedelta

from m3cli.services.validation_service import ValidationService


def parse_and_set_date_range(parameters) -> None:
    """
    Parse 'from'/'to' or 'year'/'month'/'day' parameters into validated date range

    :param parameters: dict containing request parameters
    :return: None (modifies parameters dict in-place)
    :raises ValueError, AssertionError: if parameter combinations or values are invalid
    """
    validation_service = ValidationService()

    use_from_to = 'from' in parameters and 'to' in parameters
    use_year_month = 'year' in parameters and 'month' in parameters
    contain_range = any(p in parameters for p in ('from', 'to'))
    contain_date = any(p in parameters for p in ('year', 'month', 'day'))

    if contain_range and contain_date:
        raise ValueError("Cannot mix 'from'/'to' with 'year'/'month'/'day'")
    if not use_from_to and not use_year_month:
        raise ValueError("Requires 'from'/'to' or 'year'/'month' parameters")

    if use_from_to:
        from_date = parameters.get('from')
        to_date = parameters.get('to')
        if from_date >= to_date:
            raise AssertionError('"from" must be earlier than "to"')
        return

    year = parameters.pop('year')
    month = parameters.pop('month')
    day = parameters.pop('day', None)

    try:
        year_int = int(year)
        month_int = int(month)
        day_int = int(day) if day is not None else 1
        datetime(year_int, month_int, day_int)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid date parameters: {e}") from e

    if day:
        from_date_str = f'{int(day):02d}.{month_int:02d}.{year_int}'
        from_date = validation_service.adapt_date(from_date_str)

        next_day_date = \
            datetime(year_int, month_int, int(day)) + timedelta(days=1)
        to_date_str = (
            f'{next_day_date.day:02d}.{next_day_date.month:02d}'
            f'.{next_day_date.year}'
        )
        to_date = validation_service.adapt_date(to_date_str)
    else:
        from_date_str = f'01.{month_int:02d}.{year_int}'
        from_date = validation_service.adapt_date(from_date_str)

        if month_int == 12:
            next_month, next_year = 1, year_int + 1
        else:
            next_month, next_year = month_int + 1, year_int

        to_date_str = f'01.{next_month:02d}.{next_year}'
        to_date = validation_service.adapt_date(to_date_str)

    parameters['from'] = from_date
    parameters['to'] = to_date


def validate_disabled_until_date(
        timestamp: float | None = None,
) -> None:
    """
    Validate that disabledUntil timestamp is in the future and within one month.

    :param timestamp: Unix timestamp in milliseconds (as float or int)
    :raises ValueError: If date is invalid, not in the future, or beyond one month
    """
    if not timestamp:
        return  # Optional parameter

    try:
        # Convert milliseconds timestamp to datetime
        disabled_date = datetime.fromtimestamp(timestamp / 1000).date()
    except (ValueError, TypeError, OSError) as e:
        raise ValueError(
            f"Invalid timestamp: '{timestamp}'. Error: {str(e)}"
        )

    # Get today's date
    today = datetime.now().date()

    # Check if date is in the future
    if disabled_date <= today:
        raise ValueError(
            f"The '--disabled-until' date must be in the future. "
            f"Provided: '{disabled_date.strftime('%d.%m.%Y')}'. "
            f"Today: '{today.strftime('%d.%m.%Y')}'"
        )

    # Check if date is within one month from today
    one_month_later = today + timedelta(days=30)
    if disabled_date > one_month_later:
        raise ValueError(
            f"The '--disabled-until' date must be within one month from today. "
            f"Provided: '{disabled_date.strftime('%d.%m.%Y')}'. "
            f"Maximum allowed: '{one_month_later.strftime('%d.%m.%Y')}'"
        )
