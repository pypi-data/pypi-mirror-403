import os
import sys
import logging
from datetime import datetime

class StreamToLogger:
    """
    File-like object that redirects writes (e.g. from print())
    to a logging.Logger instance.

    This class is designed to be SAFE:
    - It avoids infinite recursion if the logger itself fails
    - It remains compatible with pytest stdout/stderr capturing
    """

    def __init__(self, logger, log_level=logging.INFO, fallback_stream=None):
        """
        Parameters
        ----------
        logger : logging.Logger
            The logger that will receive redirected output.
        log_level : int
            Logging level used for redirected messages (INFO, ERROR, ...).
        fallback_stream : file-like, optional
            Real stream (usually sys.__stdout__ or sys.__stderr__) used
            as a last-resort fallback if logging fails.

        Why fallback_stream matters:
        ----------------------------
        If logging raises an exception while handling a message,
        writing to the fallback stream prevents infinite recursion
        (logger -> stderr -> logger -> ...).
        """
        self.logger = logger
        self.log_level = log_level
        self.fallback_stream = fallback_stream or sys.__stderr__

    def write(self, buf):
        """
        Called whenever something writes to this stream, e.g.:

            print("hello")

        The incoming buffer may contain:
        - multiple lines
        - trailing newlines
        - partial lines (depending on the caller)

        Each line is forwarded to the logger as a separate log record.
        """
        if not buf:
            return

        try:
            # Split into individual lines and drop empty ones
            for line in buf.rstrip().splitlines():
                if line:
                    self.logger.log(self.log_level, line)

        except Exception:
            # CRITICAL SAFETY NET:
            # If logging fails for any reason (formatter error,
            # closed handler, pytest capture issues, etc.),
            # write directly to the real stream to avoid recursion.
            self.fallback_stream.write(buf)

    def flush(self):
        """
        Required for file-like compatibility.

        Many libraries (including logging and pytest) call flush(),
        so this method must exist even if it does nothing.
        """
        pass


def setup_logger(file_name_suffix: str = 'logger', path_logger: str = os.getcwd()):
    """
    Set up a logger that writes messages both to the console (stdout)
    and to a timestamped log file.

    Parameters
    ----------
    file_name_suffix : str, optional
        A custom suffix for the log file name (default: 'logger').
        The final file name will be of the form:
        '<file_name_suffix>_YYYY-MM-DD_HH-MM-SS.txt'.

    path_logger : str, optional
        Directory path where the log file will be stored
        (default: current working directory).

    Returns
    -------
    logger : logging.Logger
        Configured logger instance that writes to both console and
        the generated log file.
    """

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logfile = os.path.join(path_logger, f"{file_name_suffix}_{timestamp}.txt")

    logger = logging.getLogger("RedirectedOutput")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # File handler (timestamped name)
    file_handler = logging.FileHandler(logfile, mode="w")
    file_handler.setFormatter(formatter)

    # Console handler (real-time stdout)
    console_handler = logging.StreamHandler(sys.__stdout__)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
