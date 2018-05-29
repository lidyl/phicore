phicore
=======

|travis| |appveyor|

phicore is a Python 3.5+ package designed to save and organize spatio-temporal laser metrology data.

See the documentation for more details https://lidyl.github.io/phicore/doc/stable/

Installation
------------

Prerequisites
^^^^^^^^^^^^^

Phicode requires the following dependencies,

- numpy >=1.10
- h5py >=2.7
- pytables >=3.4
- xarray >=0.9

To install them with conda (recommended) run,

.. code::

   conda install --file requirements.txt

alternatively to use pip,

.. code::

   pip install -r requirements.txt

Installing phicore
^^^^^^^^^^^^^^^^^^

Phicore can be installed with,

.. code::

   pip install -e .


License
-------

Copyright LIDYL CEA 2018-present, released under the CeCILL-B license (BSD-like).


See `LICENSE <./LICENSE>`_ file for more information.

.. |travis| image:: https://travis-ci.org/lidyl/phicore.svg?branch=master
    :target: https://travis-ci.org/lidyl/phicore

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/lidyl/phicore?svg=true
    :target: https://ci.appveyor.com/project/ajeandet/phicore/branch/master
