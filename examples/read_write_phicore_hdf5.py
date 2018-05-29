"""
Creating and reading phicore HDF5 files
=======================================

In thus example we will create a sample phicore HDF5 files then read
it back as ``xarray.DataArray``
"""

import numpy as np
import xarray as xr

from phicore.io import PhiDataFile


rng = np.random.RandomState(42)

Nx, Ny, Nw = 5, 5, 3

X = xr.DataArray(rng.rand(Nx, Ny, Nw),
                 dims=['x', 'y', 'w'],
                 coords={'x': np.arange(Nx), 'y': np.arange(Ny),
                         'w': np.linspace(2.3, 2.5, Nw)},
                 attrs={'scale_units': {'x': 'px', 'y': 'px', 'w': 'PHz.rad'}},
                 name='X')

#############################################################################
#
# The ``xarray.DataArray`` that we will use as an example, is as follows,
print(X)


fh = PhiDataFile('test_file.h5', 'w', force=True)
fh.write_xarray(X)


#############################################################################
#
# Now we will load this data back,


fh = PhiDataFile('test_file.h5', 'r')


X_out = fh.read_xarray('/data/X')

print(X)
