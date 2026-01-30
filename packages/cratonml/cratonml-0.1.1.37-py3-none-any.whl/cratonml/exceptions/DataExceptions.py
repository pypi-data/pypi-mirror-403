"""Модуль исключений при работе с данными(гриды, кубы, скважины, контуры)."""


class DataException(BaseException):
    """Базовый класс исключений при работе с данными(гриды, кубы, скважины, контуры)."""

    pass


class EmptyInputDataException(DataException):
    """"""

    pass
