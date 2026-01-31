Backends
========

uNAC allows to compare the output of several tools, which we refer to as backends.
You may only install those backends, that you need, as described in :doc:`installation`

Naive
-----

This is uNAC own implementation of the classical correction algorithm in its most straightforward way.
It is very fast, but has no safeguards or checks.
Currently it can only handle MS at nominal resolution

isocor
------

This backend uses the python based `isocor <https://github.com/MetaSys-LISBP/IsoCor/>` a very mature tool that handles MS data at arbitrary resolution.


IsoCorrectoR
------------

This backend uses the R based `IsoCorrectoR <https://bioconductor.org/packages//release/bioc/html/IsoCorrectoR.html>` a very powerful tool able to handle MS and MSMS data at arbitrary resolution

ICT
---

This backend uses the perl based Isotope Correction Toolbox `ICT <https://github.com/jungreuc/isotope_correction_toolbox/>` a legacy tool, correcting MS and MSMS data at nominal resolution
