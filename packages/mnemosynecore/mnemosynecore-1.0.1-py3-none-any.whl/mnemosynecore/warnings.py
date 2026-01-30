import warnings


def old_function():
    warnings.warn(
        "Пример ворнинга для устареших функций",
        DeprecationWarning,
        stacklevel=2
    )