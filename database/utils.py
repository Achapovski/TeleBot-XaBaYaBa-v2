from sqlalchemy import func, case


def get_current_date_config():
    now = func.now()

    _case = case(
        (func.extract("quarter", now) < 3, 1),
        else_=2,
    )

    return func.concat(
        func.extract("doy", now), ".", func.extract("week", now), ".", func.extract("month", now), ".",
        func.extract("quarter", now), ".", _case, ".", func.extract("year", now)
    )
