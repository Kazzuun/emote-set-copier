class SeventvError(Exception):
    pass


class RestError(SeventvError):
    pass


class UnprivilegedError(SeventvError):
    pass


class ConflictError(SeventvError):
    pass


class EmoteNotFoundError(SeventvError):
    pass


class CapacityError(SeventvError):
    pass


class OtherError(SeventvError):
    pass
