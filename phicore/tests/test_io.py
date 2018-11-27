# CeCILL-B license LIDYL, CEA

import os
import shutil

import warnings

import numpy as np
import xarray as xr
import pytest

from phicore.io import PhiDataFile


@pytest.fixture
def new_xarray():

    rng = np.random.RandomState(42)

    data_name = 'test_data'
    data = rng.rand(100, 110, 120)
    scale_units = {'x': 'px', 'y': 'px', 'f': 'px'}

    data_inst = xr.DataArray(data,
                             coords={'x': np.linspace(0, 1, 100),
                                     'y': np.linspace(0.2, 0.9, 110),
                                     'f': np.linspace(0.6, 10, 120)},
                             dims=['x', 'y', 'f'],
                             attrs={'name': data_name,
                                    'scale_units': scale_units},
                             name=data_name)
    return data_inst


@pytest.fixture
def example_dataset(tmpdir_factory, new_xarray):
    tmp_dir = tmpdir_factory.mktemp('tmp')

    data_inst = new_xarray

    fname = str(tmp_dir / 'test.h5')

    file_inst = PhiDataFile(fname, "w")

    file_inst.write_xarray(data_inst, location='/data/')
    yield fname
    # clean up the temporary folder
    try:
        shutil.rmtree(str(tmp_dir))
    except PermissionError:  # noqa: F821
        warnings.warn('PermissionError: Failed to remove temporary file '
                      '%s on Windows' % str(tmp_dir))


@pytest.mark.parametrize('backend, complevel', [('pytables', 0),
                                                ('pytables', 6),
                                                ('h5py', 0)])
def test_io_xarray(tmpdir_factory, new_xarray, backend, complevel):
    tmp_dir = tmpdir_factory.mktemp('tmp')

    # save the object to disk
    file_name = "test_file.h5"

    data_inst = new_xarray
    data_name = new_xarray.name

    file_inst = PhiDataFile(str(tmp_dir / file_name), "w")
    assert file_name in os.listdir(str(tmp_dir))

    file_inst.write_xarray(data_inst, location='/data/',
                           complevel=complevel, backend=backend)

    # read the object from disk
    file_inst_2 = PhiDataFile(str(tmp_dir / file_name), "r")
    # make sure the compression settings were correctly used
    with file_inst_2.open('r', backend='pytables') as fh:
        h5_filters = getattr(fh.root.data, data_name).filters
        assert h5_filters.fletcher32
        assert h5_filters.complevel == complevel

    data_inst_2 = file_inst_2.read_xarray('/data/' + data_name,
                                          backend=backend)

    # check that list_xarray() returns data_name
    assert "/data/"+data_name in file_inst.list_xarray()

    # check that we retrieve the original object
    xr.testing.assert_identical(data_inst, data_inst_2)
    shutil.rmtree(str(tmp_dir))


@pytest.mark.parametrize('backend', ['pytables', 'h5py'])
def test_io_xarray_preserves_attrs(tmpdir_factory, new_xarray, backend):

    tmp_dir = tmpdir_factory.mktemp('tmp')

    file_name = "test_file.h5"

    X = new_xarray
    X.attrs['a'] = 'test'
    X.attrs['c'] = np.array('üy')
    file_inst = PhiDataFile(str(tmp_dir / file_name), "w")
    file_inst.write_xarray(X, backend=backend)

    X_2 = file_inst.read_xarray('/data/' + X.name,
                                backend=backend)
    # check that the file handle was closed
    assert file_inst._fh is None

    # check attributes, order doesn't matter
    assert dict(X.attrs) == dict(X_2.attrs)
    shutil.rmtree(str(tmp_dir))


@pytest.mark.parametrize('backend', ['pytables', 'h5py'])
def test_io_dask_support(tmpdir_factory, example_dataset, backend):
    da = pytest.importorskip('dask.array')

    fh = PhiDataFile(example_dataset)

    with pytest.raises(ValueError, match='cannot be used together'):
        fh.read_xarray('/data/test_data', index=(2, 2), chunks=(4, 2),
                       backend=backend)
    X1 = fh.read_xarray('/data/test_data', backend=backend)
    assert X1.chunks is None
    assert not isinstance(X1.data, da.Array)

    chunks = (50, 20, 30)
    X2 = fh.read_xarray('/data/test_data', chunks=chunks,
                        backend=backend)
    assert X2.chunks is not None
    assert isinstance(X2.data, da.Array)

    # check that we can perform computations
    assert X1.values.sum() == pytest.approx(X2.sum().compute().values)
    assert fh._fh is not None
    # reading an xarray in dask mode (when chunks are provided) does not
    # close the file handler. Her we do it manually.
    fh._fh.close()
