"""
--------------
tqdm_logger.py
--------------

This module provides utilities for redirecting TQDM (progress bar library) output to a logger.

"""
from __future__ import annotations
import io
import time
import logging


class TqdmToLogger(io.StringIO):
    """
    Output stream for TQDM which will output to logger module instead of the StdOut.

    This class provides an output stream for TQDM (progress bar library) that directs the output
    to a specified logger instead of the standard output.

    """

    #: The logger object to which the TQDM output is directed.
    logger = None
    #: The logging level to be used when emitting log messages.
    level = None
    buf = ""

    def __init__(self, logger: logging.Logger, level=logging.INFO):
        """
        Initialize the TqdmToLogger instance.

        :param logger: A logger object to which TQDM output will be directed.
        :param level: The logging level to be used (default: logging.INFO).

        This method initializes the TqdmToLogger instance with the specified logger and logging level.
        The logger is used to direct TQDM output, and the logging level determines the severity of log messages.

        Example:

        .. code-block:: python

            # Example usage of __init__ method in the TqdmToLogger class
            import logging
            from TqdmToLoggerModule import TqdmToLogger

            # Create a logger
            logger = logging.getLogger(__name__)

            # Initialize TqdmToLogger with the logger and custom logging level
            tqdm_out_logger = TqdmToLogger(logger=logger, level=logging.INFO)

        """
        super(TqdmToLogger, self).__init__()
        self.logger = logger
        self.level = level

    def write(self, buf: str):
        """
        Write the specified buffer content.

        :param buf: The buffer content to be written.
        """
        self.buf = buf.strip("\r\n\t ")

    def flush(self):
        """Execute the flush operation, logging the buffered content."""

        self.logger.log(self.level, self.buf)


if __name__ == "__main__":
    from math import sqrt

    from tqdm import tqdm
    from joblib import Parallel, delayed

    logging.basicConfig(format="%(asctime)s [%(levelname)-8s] %(message)s")
    lgr = logging.getLogger()
    lgr.setLevel(logging.DEBUG)

    tqdm_out = TqdmToLogger(lgr, level=logging.INFO)
    for x in tqdm(range(10), file=tqdm_out):
        time.sleep(0.1)

    x = Parallel(n_jobs=2)(delayed(sqrt)(i**2) for i in tqdm(range(10), file=tqdm_out))

    lgr.info(f"x: {x}")
