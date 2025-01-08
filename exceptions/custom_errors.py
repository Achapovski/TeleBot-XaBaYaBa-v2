class ParseException(Exception):
    pass


class IncorrectUserException(Exception):
    pass


class IncorrectAmountException(ParseException):
    pass


class IncorrectCategoryException(ParseException):
    pass


class IncorrectMessageText(ParseException):
    pass
