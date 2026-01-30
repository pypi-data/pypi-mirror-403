"""TREECORR_AUX.

:Name: treecorr_aux.py

:Description: This file contains methods for working with TreeCorr output files.

:Author: Martin Kilbinger <martin.kilbinger@cea.fr>

"""

import ast
import numpy as np
import treecorr


def read_ascii_to_ngcorrelation(file_path):
    """Read ASCII to NGCorrelation.

    Read TreeCorr ASCII output file and create a NGCorrelation instance
    without needing a config file. All configuration parameters are
    extracted from the ASCII file metadata.

    Parameters
    ----------
    file_path : str
        path to TreeCorr ASCII output file

    Returns
    -------
    treecorr.NGCorrelation
        TreeCorr NGCorrelation object with data loaded from ASCII file

    Raises
    ------
    IOError
        if input file is not found or cannot be read
    ValueError
        if file format is not recognized as TreeCorr ASCII output
    """
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except IOError as e:
        raise IOError(f"Cannot read file '{file_path}': {e}")

    if not lines:
        raise ValueError(f"File '{file_path}' is empty")

    # Parse the config from first line
    if not lines[0].startswith('##'):
        raise ValueError(f"File '{file_path}' does not appear to be TreeCorr ASCII output")

    # Extract config dictionary from first line
    config_str = lines[0][2:].strip()  # Remove '##' and whitespace
    try:
        config = ast.literal_eval(config_str)
    except (ValueError, SyntaxError) as e:
        raise ValueError(f"Cannot parse config from first line: {e}")

    # Verify this is an NG (gamma-gamma) correlation
    if config.get('corr') != 'NG':
        raise ValueError(f"Expected 'NG' correlation type, got '{config.get('corr')}'")

    # Create NGCorrelation object with config parameters
    ng = treecorr.NGCorrelation(
        min_sep=config['min_sep'],
        max_sep=config['max_sep'],
        sep_units=config['sep_units'],
        nbins=config['nbins'],
        var_method=config.get('var_method', 'shot'),
        metric=config.get('metric', 'Euclidean'),
    )

    # Use TreeCorr's built-in read method to load the data
    ng.read(file_path)

    return ng
