phicore
=======

phicore is a Python 3.5+ package designed to save and organize spatio-temporal laser metrology data.


Installation
------------

To install phicore with conda (recommended) run,

.. code::

   conda install --file requirements.txt

which will install the following dependencies,

- numpy >=1.10
- h5py >=2.7
- pytables >=3.4
- xarray >=0.9
- scikit-image >=0.13

alternatively to use PyPi,

.. code::

   pip install --file requirements.txt

Documentation
-------------
io.PhiDataFile
^^^^^^^^^^^^^^

.. code::python

    from phicore.io import PhiDataFile

    file_inst = PhiDataFile(fullpath, mode="r")
    X = file_inst.read_xarray('/data/Sxyw')


File format and xarray format
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

See `API.md <./API.md>`_.

Running unit tests
^^^^^^^^^^^^^^^^^^

Unit tests can be run with,

.. code::

    py.test -sv


License
-------

Copyright LIDYL CEA 2018-present, released under the CeCIL-B license (BSD-like).


See `LICENSE <./LICENSE>`_ file for more information.
