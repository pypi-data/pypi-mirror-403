Usage
=====

Command line interface
----------------------

After installation, the main entry point is the ``uNAC`` command:

.. code-block:: bash

    uNAC -c config.toml -s 0.01 input.xlsx

Options:

- ``-c/--config``: a config toml file (optional)
- ``-s``: the minimal standard deviation (optional, default 0.01)
- ``input.xlsx``: input data in special format


Config file
-----------

The config file contains information about natural abundances of different atoms,
and values for the different tolerances

.. code-block:: toml

    [natural_abundance]
    C = [0.9893, 0.0107]
    H = [0.999885, 0.000115]
    N = [0.99636, 0.00364]
    O = [0.99757, 0.00038, 0.00205]
    P = [1]
    S = [0.9499, 0.0075, 0.0425, 0, 0.0001]
    Si = [0.92223, 0.04685, 0.03092]

    [tolerance]
    diff = 0.001
    negative = 0.001

Input file
----------

TODO
