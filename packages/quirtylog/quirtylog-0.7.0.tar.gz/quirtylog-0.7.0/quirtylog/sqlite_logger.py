"""
----------------
sqlite_logger.py
----------------

This module provides the SQLiteHandler class, a thread-safe logging handler
for storing log records in an SQLite database.
"""
from __future__ import annotations
import time
import logging
import sqlite3

from logging import LogRecord
from pathlib import Path


class SQLiteHandler(logging.Handler):
    """
    Thread-safe logging handler for SQLite.

    This class extends the logging.Handler class to provide a thread-safe logging handler
    for storing log records in an SQLite database.
    """

    @property
    def log_table(self) -> str:
        """Return the name of the table in the SQLite database"""
        return self._log_table

    _log_table = "log"

    _initial_sql = f"""CREATE TABLE IF NOT EXISTS {_log_table}(
                        TimeStamp TEXT,
                        Source TEXT,
                        LogLevel INT,
                        LogLevelName TEXT,
                        Message TEXT,
                        Args TEXT,
                        Module TEXT,
                        FuncName TEXT,
                        LineNo INT,
                        Exception TEXT,
                        Process INT,
                        Thread TEXT,
                        ThreadName TEXT
                   )"""

    _insertion_sql = f"""INSERT INTO {_log_table}(
                        TimeStamp,
                        Source,
                        LogLevel,
                        LogLevelName,
                        Message,
                        Args,
                        Module,
                        FuncName,
                        LineNo,
                        Exception,
                        Process,
                        Thread,
                        ThreadName
                   )
                   VALUES (
                        '%(dbtime)s',
                        '%(name)s',
                        %(levelno)d,
                        '%(levelname)s',
                        '%(msg)s',
                        '%(args)s',
                        '%(module)s',
                        '%(funcName)s',
                        %(lineno)d,
                        '%(exc_text)s',
                        %(process)d,
                        '%(thread)s',
                        '%(threadName)s'
                   );
                   """

    def __init__(self, db: Path | str = "log.db"):
        """
        Initialize the SQLiteHandler instance.

        :param db: A path for creating the SQLite database (default: 'log.db').

        :raise TypeError: If `db` is not a string or a Path object.

        This method initializes the SQLiteHandler instance by connecting to the SQLite database specified
        by the `db` parameter. It also executes the initial SQL statement to create the log table if it does not exist.

        Example:

        .. code-block:: python

            # Initialize SQLiteHandler with the default database path
            sqlite_handler = SQLiteHandler()

            # Initialize SQLiteHandler with a custom database path
            sqlite_handler_custom = SQLiteHandler(db='/path/to/logs/my_logs.db')

        """

        logging.Handler.__init__(self)

        if isinstance(db, str):
            db = Path(db)
        elif not isinstance(db, Path):
            raise TypeError("`db` is a Path object")

        self._db = db
        conn = sqlite3.connect(self._db)
        conn.execute(self._initial_sql)
        conn.commit()

    @staticmethod
    def format_time(record: LogRecord):
        """
        Create a time-stamp for the log record.

        :param record: The log record to which the time-stamp will be added.

        This static method adds a time-stamp to the provided log record. The time-stamp is generated
        based on the `created` attribute of the log record, representing the time of log record creation.

        Example:

        .. code-block:: python

            # Example usage of format_time in the SQLiteHandler class
            log_record = logging.LogRecord('name', logging.ERROR, 'pathname', 1, 'Log message', (), None)
            SQLiteHandler.format_time(log_record)
            print(log_record.dbtime)  # Output: '2023-12-18 15:30:45' (example timestamp)

        """

        record.dbtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created))

    def emit(self, record: LogRecord):
        """
        Emit the log message by formatting and inserting the log record into the SQLite database.

        :param record: The log record to be emitted.

        This method formats the log record using the `format` and `format_time` methods, and then inserts
        the formatted log record into the SQLite database. If the log record contains exception information,
        it is formatted and stored in the `exc_text` attribute of the record.

        .. note::

            - This method assumes that the log record follows the structure expected by the SQL insertion statement.
            - The method opens a new connection to the SQLite database for each log record insertion, which may not
              be efficient in high-throughput scenarios.

        Example:

        .. code-block:: python

            # Example usage of emit in the SQLiteHandler class
            log_record = logging.LogRecord('name', logging.ERROR, 'pathname', 1, 'Log message', (), None)
            sqlite_handler = SQLiteHandler(db='/path/to/logs/my_logs.db')
            sqlite_handler.emit(log_record)

        """

        self.format(record)
        self.format_time(record)
        if record.exc_info:  # for exceptions
            record.exc_text = logging._defaultFormatter.formatException(record.exc_info)
        else:
            record.exc_text = ""

        # Insert the log record
        sql = self._insertion_sql % record.__dict__
        conn = sqlite3.connect(self._db)
        conn.execute(sql)
        conn.commit()  # not efficient, but hopefully thread-safe


if __name__ == "__main__":
    """A test script"""

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # sqlite handler
    sh = SQLiteHandler(db="test.db")
    sh.setLevel(logging.INFO)
    logging.getLogger().addHandler(sh)

    # test
    logging.info("Start")
    time.sleep(5)
    logging.info("End")
