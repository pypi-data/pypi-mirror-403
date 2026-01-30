"""LOGGING.

:Description: This script contains utility methods for job execution and
progress logging.

:Author: Martin Kilbinger <martin.kilblinger@cea.fr>

"""

import os
import sys


def log_command(argv, name=None, close_no_return=True):
    """Log Command.

    Write command with arguments to a file or stdout.
    Choose name = 'sys.stdout' or 'sys.stderr' for output on sceen.

    MKDEBUG copied from shapepipe:cfis

    Parameters
    ----------
    argv : list
        Command line arguments
    name : str
        Output file name (default: 'log_<command>')
    close_no_return : bool
        If True (default), close log file. If False, keep log file open
        and return file handler

    Returns
    -------
    filehandler
        log file handler (if close_no_return is False)

    """
    # Set log file path
    if name == "sys.stdout":
        f = sys.stdout
    elif name == "sys.stderr":
        f = sys.stderr
    else:
        if name is None:
            name = "log_" + os.path.basename(argv[0])
        f = open(name, "w")

    # Loop over arguments
    log = ""
    for a in argv:
        # Quote argument if special characters
        if "[" in a or "]" in a:
            a = f'"{a}"'

        log = f"{log}{a} "

    # Write to file except last character (space)
    print(log[:-1], file=f)

    # Return file handle if required
    if not close_no_return:
        return f

    # Close if proper file
    if not name in ("sys.stdout", "sys.stderr"):
        f.close()
