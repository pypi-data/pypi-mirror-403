Installation
============

uNAC has several :doc:`backends </backends>`, that have partially complicated dependecies.
You may install backends at your own liking.

Basic installation (naive correction backend only):

.. code-block:: bash

    pip install unac

Advanced backends
-----------------

all other backends require additional dependencies, and can be installed individually

isocor
^^^^^^

isocor has only other python dependencies, to install them run

.. code-block:: bash

    pip install unac[isocor]

IsoCorrectoR
^^^^^^^^^^^^

IsoCorrectoR is R based and therefore requires R to be installed.
To bridge to python rpy2 is used (which fails to install without a running R)
Additionally further R packages need to be installed through uNAC-setup (which takes a couple of minutes)

So with R installed run

.. code-block:: bash

    pip install unac[isocorrector]
    uNAC-setup


ICT
^^^

ICT is perl based and therefore requieres a running perl. No other dependencies are needed.
If perl is installed ICT can be used directly


Complete Installation
^^^^^^^^^^^^^^^^^^^^^

To install all backends

- install R
- install perl
- pip install unac[isocor,isocorrector]

System requirements
-------------------

- Python >= 3.11
- Perl (for ICT backend)
- R (for IsoCorrectoR backend)
