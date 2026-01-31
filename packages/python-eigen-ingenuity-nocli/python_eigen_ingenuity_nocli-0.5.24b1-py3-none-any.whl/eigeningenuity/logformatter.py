import datetime
import traceback
import sys
import logging


# Function to add the filename to each line of the traceback
def format_traceback(exc_type, exc_value, exc_traceback, filename, configfile):
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    tb_lines2 = []
    tb_lines2.append(
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
        + " - "
        + filename
        + configfile
        + " - ERROR - An Error Occurred\n"
    )
    for line in tb_lines:
        x = line.split("\n")
        for y in x:
            if y != "":
                tb_lines2.append(
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
                    + " - "
                    + filename
                    + configfile
                    + " - ERROR - "
                    + y
                    + "\n"
                )
    tb_lines2.append(
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
        + " - "
        + filename
        + configfile
        + " - ERROR - Finished Executing\n"
    )
    return "".join(tb_lines2)


def exception_formatter(exc_type, exc_value, exc_traceback, filename, configfile=""):
    if configfile != "":
        configfile = ":" + configfile
    tb_formatted = format_traceback(
        exc_type, exc_value, exc_traceback, filename, configfile
    )
    print(tb_formatted)


sys.excepthook = exception_formatter


def log_handler(filename, configfile=""):
    if configfile != "":
        configfile = ":" + configfile
    stream_handler = logging.StreamHandler(
        sys.stdout
    )  # By default, it logs to sys.stderr, but you can specify stdout.
    stream_handler.setLevel(logging.INFO)  # Set the log level for the stream handler
    stream_formatter = logging.Formatter(
        f"%(asctime)s - {filename}{configfile} - %(levelname)s - %(message)s"
    )
    stream_handler.setFormatter(stream_formatter)

    # Get the root logger and add the stream handler to it
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(stream_handler)


def setup_logging(filename, configfile=""):
    """Set up all logging, warning, and exception handling in one call."""
    import warnings
    import os

    # Extract just the filename if a full path is provided
    if "/" in filename or "\\" in filename:
        filename = os.path.basename(filename)

    if "/" in configfile or "\\" in configfile:
        configfile = os.path.basename(configfile)

    # Set up logging handler
    log_handler(filename, configfile)

    # Set up custom warning handler
    def custom_warning_handler(
        message, category, warn_filename, lineno, file=None, line=None
    ):
        logging.warning(f"{message}\n")

    warnings.filterwarnings("always", category=Warning, append=True)
    warnings.showwarning = custom_warning_handler

    # Set up custom exception handler
    def custom_exception_handler(exc_type, exc_value, exc_traceback):
        exception_formatter(exc_type, exc_value, exc_traceback, filename, configfile)

    sys.excepthook = custom_exception_handler
