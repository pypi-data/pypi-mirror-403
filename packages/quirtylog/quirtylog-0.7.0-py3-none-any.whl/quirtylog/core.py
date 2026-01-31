"""
-------
core.py
-------

This module contains utility functions for logging and file management.

.. note::

    The module includes functions for logging configuration, exception handling, variable name retrieval,
    path construction, path validation, and clearing old log files.

    Ensure to review the individual docstrings for each function for detailed information and usage examples.

"""
from __future__ import annotations
import re
import time
import inspect
import logging
import functools
import logging.config

from pathlib import Path

import yaml
import coloredlogs

from .sqlite_logger import SQLiteHandler

__all__ = [
    "configure_logger",
    "create_logger",
    "measure_time",
    "display_arguments",
    "clear_old_logs",
]

path_matcher = re.compile(r"\$\{([^}^{]+)\}")


def _serve_default_log_path() -> Path:
    return Path().absolute() / "logs"


def _serve_default_config_path() -> Path:
    return Path(__file__).absolute().parent / "logging.yaml"


def retrieve_name(var) -> str:
    """
    Retrieve the name of a variable as a string.

    This function inspects the local variables in the calling frame to find the name
    associated with the provided variable.

    :param var: The input variable for which the name needs to be retrieved.

    :return: The name of the variable as a string.

    .. note::

        This function relies on inspecting the local variables of the calling frame,
        and it may not work correctly in all scenarios (e.g., if the variable is not in the local scope).
        Use with caution and consider the context of its usage.

    Example:

    .. code-block:: python

        x = 42
        variable_name = retrieve_name(x)
        print(variable_name)  # Output: 'x'

    """

    callers_local_vars = inspect.currentframe().f_back.f_locals.items()
    try:
        return [var_name for var_name, var_val in callers_local_vars if var_val is var][0]
    except IndexError:
        return "unknown"


def path_constructor(loader, node, log_path: str | Path = "logs") -> str:
    """
    YAML constructor function for expanding and replacing paths.

    This function is used as a constructor in YAML loading to extract a matched value, expand environment variables,
    and replace the match with the provided log path.

    :param loader: The YAML loader instance.
    :param node: The YAML node representing the value to be processed.
    :param log_path: The base path to be used for constructing the full path (default: 'logs').

    :return: A valid path obtained by expanding environment variables and replacing the matched value.

    .. note::

        - This function is intended for use with the PyYAML library to customize the loading of YAML files.
        - The `log_path` parameter is used as the base path for constructing the full path.
        - The function utilizes a regular expression match to identify and replace the matched value.

    Example:

    .. code-block:: python

        yaml.add_constructor(
            '!path',
            lambda loader, node: path_constructor(loader, node, log_path='/custom/logs')
        )


    """
    value = node.value
    match = path_matcher.match(value)
    if match:
        return str(log_path) + value[match.end() :]
    return str(value)


def check_path(var: str | Path, name: str = "value") -> Path:
    """
    Validate and convert the input value to a Path object.

    This function tests the input value parameter, ensuring it is either a string or a Path object.
    If the input is a string, it is converted to a Path object. If it is already a Path object, the function
    performs a type check to confirm its validity.

    :param var: The input value, which can be either a string or a Path object.
    :param name: The name of the input variable, used in error messages (default: 'value').

    :return var: A Path object representing the validated input value.

    :raise TypeError: If the input is not a string or a Path object.

    Example:

    .. code-block:: python

        file_path = check_path('/path/to/file.txt', name='file_path')
        print(file_path)  # Output: PosixPath('/path/to/file.txt')

    """
    if isinstance(var, str):
        var = Path(var)
    elif not isinstance(var, Path):
        raise TypeError(f"`{name}` must be a str or Path object")
    return var


def configure_logger(
    log_path: str | Path | None = None, config_file: str | Path | None = "default"
):
    """
    Configure an existing log

    :param log_path: The folder path for storing log files. Defaults to `logs/`.
    :param config_file: The configuration file path. Defaults to `default`.
        If `config_file` is provided, the logger is configured using the YAML configuration file;
        otherwise, a basic configuration is applied.


    Example:

    .. code-block:: python

        import logging

        my_logger = logging.getLogger(name='my-logger')

        configure_logger(
            log_path='/path/to/logs',
            config_file='/path/to/config.yaml'
        )

    """

    if log_path is None:
        log_path = _serve_default_log_path()
    log_path = check_path(var=log_path, name=retrieve_name(log_path))
    log_path.mkdir(parents=True, exist_ok=True)

    coloredlogs.install()
    if config_file is not None:
        if config_file == "default":
            config_file = _serve_default_config_path()

        config_file = check_path(var=config_file, name=retrieve_name(config_file))

        yaml.add_implicit_resolver("!path", path_matcher)
        yaml.add_constructor(
            "!path",
            lambda loader, node: path_constructor(loader, node, log_path=log_path),
        )
        with open(config_file, "r") as file:
            # add the new path loader
            config = yaml.load(file, Loader=yaml.FullLoader)
            logging.config.dictConfig(config)
    else:
        base_config = dict(
            version=1,
            disable_existing_loggers=False,
            loggers={
                "": {"level": "INFO"},
                "another.module": {
                    "level": "DEBUG",
                },
            },
        )
        logging.config.dictConfig(base_config)

    #


def create_logger(
    log_path: str | Path | None = None,
    config_file: str | Path | None = "default",
    name: str | None = None,
    db: str | Path | None = None,
    remove_old_log: bool = True,
    k_min: int | str = 1,
) -> logging.Logger:
    """
    Create a custom logger object with optional configuration parameters.

    :param log_path: The folder path for storing log files. Defaults to `logs/`.
    :param config_file: The configuration file path. Defaults to `default`.
        If `config_file` is provided, the logger is configured using the YAML configuration file;
        otherwise, a basic configuration is applied.
    :param name: The logger name. If None, it is automatically determined based on the calling module and function.
    :param db: The name of the SQLite database. If provided, a SQLiteHandler will be added to the logger.
    :param remove_old_log: A flag indicating whether to remove old log files from the specified log path.
    :param k_min: The minimum number of log files to keep in the history (default: 1).
            If `k_min` is a string, it will be converted to an integer.

    :return: The custom logger object.

    :raise TypeError: If `name` is not a string.

    Example:

    .. code-block:: python

        path = '/path/to/logs'
        config = 'logging_config.yml'
        name = 'my_logger'
        db = 'log.db'
        custom_logger = create_logging(log_path=path, config_file=config, name=name, db=db)
        custom_logger.info('Custom logger initialized successfully.')

    """

    if log_path is None:
        log_path = _serve_default_log_path()
    log_path = check_path(var=log_path, name=retrieve_name(log_path))

    if remove_old_log:
        clear_old_logs(log_path=log_path, k_min=k_min)

    if name is None:
        stack = inspect.stack()
        if len(stack) > 1:
            calling_frame = stack[1]
            calling_frame_name = calling_frame[1].replace(".py", "")
            # by default, we consider only the last two stack
            calling_frame_name = ".".join(calling_frame_name.split("/")[-2:])

            module = inspect.getmodule(calling_frame[0])
            if module is not None:
                calling_function_name = module.__name__
            else:
                calling_function_name = "__main__"

            if calling_frame_name != calling_function_name:
                name = f"{calling_frame_name}.{calling_function_name}"
            else:
                name = calling_function_name

        else:
            # here in the main thread in REPL
            name = "__main__"

    elif not isinstance(name, str):
        raise TypeError("`name` is str")

    configure_logger(log_path=log_path, config_file=config_file)
    # Here is needed to get the logging object
    logger = logging.getLogger(name=name)

    if db is not None:
        db = log_path / db
        sql_handler = SQLiteHandler(db=db)
        sql_handler.setLevel(logging.INFO)
        logger.addHandler(sql_handler)

    return logger


def measure_time(logger: logging.Logger, level: str = "info"):
    """
    Create a decorator for computing execution time and managing exceptions with a specified logger.

    This decorator wraps the provided function measuring time, logging any exceptions that occur during its execution.

    :param logger: The logging object to be used for logging exceptions.
    :param level: The logging level for info messages (default: 'info').
        Possible values: {'info', 'debug', 'warning', 'error'}.

    :return: The decorator function.

    Usage:

    .. code-block:: python

        @measure_time(logger=my_logger, level='error')
        def my_function():
            # Function implementation

    .. note::

        - The decorator logs the total execution time of the wrapped function and any exceptions that occur.
        - Exceptions are logged with their class name, error message, and stack trace.
        - The decorator re-raises the exception after logging.

    Example:

    .. code-block:: python

        @measure_time(logger=my_logger, level='error')
        def divide(a, b):
            return a / b

        result = divide(10, 0)  # Logs the exception and raises it

    """
    lgr = getattr(logger, level)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__

            try:
                start = time.time()
                result = func(*args, **kwargs)
                dt = time.time() - start

                lgr(f"`{func_name}` executed. Total time {dt:.3f} [s]")
                return result

            except Exception as e:
                # log the exception
                err = f"Error in `{func_name}`. {e.__class__.__name__}: {e}"
                logger.error(err, exc_info=True)

                # re-raise the exception
                raise e

        return wrapper

    return decorator


def display_arguments(logger: logging.Logger, level: str = "info"):
    """
    Create a decorator for showing information about function signature with a specified logger.

    This decorator wraps the provided function measuring time, logging arguments.

    :param logger: The logging object to be used for logging exceptions.
    :param level: The logging level for info messages (default: 'info').
        Possible values: {'info', 'debug', 'warning', 'error'}.

    :return: The decorator function.

    Usage:

    .. code-block:: python

        @display_arguments(logger=my_logger, level='error')
        def my_function():
            # Function implementation


    Example:

    .. code-block:: python

        @display_arguments(logger=my_logger, level='error')
        def my_sum(a, b):
            return a + b

        result = my_sum(10, b=0)  # Logs my_sum(a=10, b=0)

    """
    lgr = getattr(logger, level)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_args = inspect.signature(func).bind(*args, **kwargs).arguments
            func_args_str = ", ".join(map("{0[0]}={0[1]!r}".format, func_args.items()))

            lgr(
                f"Executing function {func.__module__}.{func.__qualname__}({func_args_str})"
            )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def clear_old_logs(log_path: str | Path | None = None, k_min: str | int = 1):
    """
    Delete old log files in the specified folder.

    This function removes log files with filenames in the format "<name>.log.<digit>",
    keeping a minimum number of log files specified by the parameter `k_min`.

    :param log_path: The folder path where log files are stored (default: 'logs').
    :param k_min: The minimum number of log files to keep in the history (default: 1).
        If `k_min` is a string, it will be converted to an integer.

    .. note::

        - The function utilizes the `check_path` function to validate and convert the `log_path` parameter.
        - Log files with filenames in the format "<name>.log.<digit>" are considered for deletion.
        - The parameter `k_min` determines the minimum number of log files to retain; older files are deleted.
        - If the log folder does not exist, no files are removed.

    Example:

    .. code-block:: python

        # Remove log files in the '/path/to/logs' folder, keeping at least 2 files in the history
        clear_old_logs(log_path='/path/to/logs', k_min=2)

    """
    if log_path is None:
        log_path = _serve_default_log_path()

    log_path = check_path(var=log_path, name=retrieve_name(log_path))
    if isinstance(k_min, str):
        k_min = int(k_min)

    if log_path.exists():
        # TODO to be changed: notice the loggers section in yml file
        # select files with format <name>.log.<digit>
        for p in log_path.iterdir():
            number = str(p).split(".")[-1]
            if number.isdigit() and p.is_file():
                if int(number) > k_min:
                    # then remove files
                    try:
                        p.unlink()
                    except Exception:
                        pass


if __name__ == "__main__":
    pass
