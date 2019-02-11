# CeCILL-B license LIDYL, CEA

import os
import time
import warnings
import operator

from collections import namedtuple

from typing import Optional, Tuple, List, Dict, Any


__fileformatversion__ = 2


class PhiDataFile(object):
    def __init__(self, fullpath: str, mode: str = "r", force: bool = False):
        """Defines the structure of some archived data and methods
        associated to Input and Output.

        Parameters
        ----------
        fullpath : str
          path to the file. If the full path contains the token "{date}" it
          will be replaced by the current date
        mode : str
          the mode in which to open the file see documentation of `open`
        force : bool
          overwrite a file even if it exists
        """
        self.fullpath = fullpath.replace('{date}',
                                         time.strftime('%Y-%m-%d-%H%M%S'))

        if mode not in ('r', 'r+', 'w', 'w+', 'a', 'a+'):
            raise ValueError('Access type {} unkown. See `open` documentation.'
                             .format(mode))
        self.mode = mode

        if not os.path.exists(self.fullpath) and\
                mode in ('r', 'r+', 'a', 'a+'):
            raise IOError('Cannot read/append {} as it does not exist!'
                          .format(self.fullpath))
        elif os.path.exists(self.fullpath) and mode in ('w', 'w+'):
            if not force:
                raise IOError(('Attempting to write to file {} '
                               'but it already exists. Use force=True.')
                              .format(self.fullpath))

        # ## Error checking
        # TODO
        # * file is not phidata compatible

        # Create file if necessary
        if self.mode in ("w", "w+"):
            self._create_file()

    def open(self, mode: Optional[str] = None, backend: str = 'h5py',
             filters=None):
        """ Open the hdf5 file

        Parameters
        ----------
        mode : str
          mode in which to open the file. By default,
          use the mode setting provided at initialization
        backend : str
          hdf5 backend to use {"h5py", "pytables"}
        filter: obj
          An instance of the Filters class (for compression, etc)
        """
        if mode is None:
            if self.mode in ('w', 'w+'):
                mode = 'a'
            else:
                mode = self.mode
        if mode in ('w', 'w+'):
            raise IOError(("Writing would overwrite the file {} "
                           " and is not supported. This can only be "
                           "done in the class initialization. Use mode='a' "
                           "instead!")
                          .format(self.fullpath))

        if backend == 'h5py':
            import h5py
            return h5py.File(self.fullpath, mode)
        elif backend == 'pytables':
            import tables as tb
            return tb.open_file(self.fullpath, mode=mode, filters=filters)
        else:
            raise ValueError("Wrong backend {}".format(backend))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def _create_file(self) -> None:
        """Initialize basic file structure"""
        import h5py
        with h5py.File(self.fullpath, 'w') as f:
            f.create_group('data')
            f.create_group('scales')
            f.create_group('diag')
            f.attrs['rev_fileformat'] = __fileformatversion__

    def create_group(self, name: str, location: Optional[str] = None):
        """ Create a new dataset see h5py.Group.create_group """
        with self.open('a') as fh:
            if location is None:
                out = fh.create_group(name)
            else:
                out = fh[location].create_group(name)
        return out

    def create_dataset(self,
                       name: str,
                       data,
                       fletcher32: bool = True,
                       complib: str = 'blosc:lz4',
                       complevel: int = 0,
                       chunks: bool = None,
                       backend: str = 'pytables',
                       **args):
        """ Create a new dataset see h5py.Group.create_dataset

        Parameters
        ----------
        args : kwargs
          see keyword arguments from h5py.Group.create_dataset

        fletcher32 : bool
          use fletcher32 checksums

        complib : str
          compression library to use (see pytables.Filters)

        complevel : str
          the compression level (see pytables.Filters)

        chunks : bool
           chunk shape, to enable auto-chunking set to True or None
           with h5py, or to None with Pytables

        backend : str
          the backend to use
        """
        if backend == 'pytables':
            import tables as tb
            filters = tb.Filters(fletcher32=fletcher32, complib=complib,
                                 complevel=complevel)
            with self.open('a', backend='pytables') as fh:
                base_location, array_name = os.path.split(name)
                out = fh.create_carray(base_location, array_name,
                                       obj=data, chunkshape=chunks,
                                       filters=filters)
        elif backend == 'h5py':
            if complevel > 0:
                raise ValueError("The h5py backend doesn't support "
                                 "compression, either set the backend "
                                 "to 'pytables' or 'complevel' to 0.")
            with self.open('a', backend='h5py') as fh:
                out = fh.create_dataset(name, data=data, chunks=chunks,
                                        fletcher32=fletcher32, **args)
        else:
            raise ValueError("Wrong backend {}".format(backend))
        return out

    def write_attrs(self,
                    attrs: dict,
                    location: Optional[str] = None) -> None:
        """ Write attributes to a h5 node

        Parameters
        ----------
        attrs : dict
          the attributes to set
        location : str
          location path inside the hdf5
        """

        with self.open('a') as fh:
            if location is None:
                fh_attrs = fh.attrs
            else:
                fh_attrs = fh[location].attrs

            for key, val in attrs.items():
                fh_attrs[key] = val

    def get_attrs(self,
                  location: Optional[str] = None) -> Dict[str, Any]:
        """ Returns all attrs in specified location, as a dict.

        Parameters
        ----------
        location : str
            location path inside the hdf5 file. If None, get_attrs returns
            head attributes.

        """

        with self.open('r') as fh:
            if location is None:
                attrs = fh.attrs
            else:
                attrs = fh[location].attrs

            return {key: val for key, val in attrs.items()}

    def list_xarray(self, location: str = '/data/') -> List[str]:
        """ List valid xarrays in designated folder. Returns full path.

        Parameters
        ----------
        location : str
          Where to look for xarrays. Default if not specified is "/data/"

        """

        output_list = list()

        if not location.endswith('/'):
            location += '/'

        with self.open('r', backend='h5py') as fh:
            for dset in fh[location].keys():
                if "scales" in fh[location + dset].attrs:
                    output_list.append(fh[location + dset].name)

        return output_list

    def write_xarray(self,
                     data,
                     location: str = '/data/',
                     chunks: bool = None,
                     backend: str = 'pytables',
                     complib: str = "blosc:lz4",
                     complevel: int = 0,
                     **args) -> None:
        """ Write an xarray to hdf5

        Parameters
        ----------
        data : xarray.DataArray
          the data to save

        location : str
          path in the hdf5 file in which to save

        args : kwargs
          other keyword arguments to pass to h5py.Group.create_array

        fletcher32 : bool
          use fletcher32 checksums

        complib : str
          compression library to use (see pytables.Filters)

        complevel : str
          the compression level (see pytables.Filters)

        chunks : bool
           chunk shape, to enable auto-chunking set to True or None
           with h5py, or to None with Pytables

        backend : str
          the backend to use
        """
        import numpy as np

        if data.name is not None:
            dataset_name = data.name
        else:
            warnings.warn("The dataset name should be specified as data.name, "
                          "storing it in data.attrs['name'] is deprecated and "
                          "will be removed in version 0.4.",
                          DeprecationWarning)
            dataset_name = data.attrs['name']
        location = os.path.join(location, dataset_name)
        if not dataset_name:
            raise ValueError(('Not a valid path {} inside hdf5 for saving '
                              'xarrays. Must be of the form '
                              '/data/<array_name>.').format(location))
        # Create the dataset with the corresponding backend (and compression)
        self.create_dataset(location, data=data.values, chunks=chunks,
                            backend=backend, complib=complib,
                            complevel=complevel, **args)
        # Always use h5py to set attributes and scales (to use a simpler API)
        with self.open('a') as fh:
            fh[location].attrs['name'] = dataset_name
            fh[location].attrs['scales'] = [el.encode('utf8')
                                            for el in data.dims]
            for key, val in data.coords.items():
                scale_path = '/scales/' + '_'.join([dataset_name, key])
                fh.create_dataset(scale_path, data=val.values, **args)
                fh[scale_path].attrs['unit'] = data.attrs['scale_units'][key].encode('utf-8')  # noqa

            # save optional attributes
            for key, value in data.attrs.items():
                if key in ['name', 'scale_units']:
                    continue

                if (isinstance(value, (np.ndarray, np.str_))
                        and value.dtype.kind == 'U'
                        and value.ndim == 0):
                    value = str(value)

                fh[location].attrs[key] = value

    def read_xarray(self,
                    location: str,
                    index: Tuple[int, ...] = (),
                    chunks: Tuple[int, ...] = (),
                    backend: str = 'h5py',
                    mmap: bool = False):
        """ Read an xarray from hdf5

        Only one of ``index``, ``chunks`` can be provided at a time.

        Parameters
        ----------
        location : str
          path in the hdf5 file
        index : tuple
          tuple of slices specifying the subset of the dataset to load
        chunks : tuple, optional
            If chunks is provided, it is used to load the new dataset into dask
            arrays. chunks=() loads the dataset with dask using a single
            chunk for all arrays.
        backend : str
          the backend to use, one of {'hdf5', 'pytables'}
        mmap : bool, default=False
          if True return a memory map of the data. To obtain
          a numpy array it is sufficient to slice or perform calculations
          with the obtained object.

          .. note:: this option is not compatible with index or chunks,
          and returns a namedtuple (with the idential fields) instead
          of a real DataArray.

        Returns
        -------
        X : {xarray.DataArray, namedtuple}
          returns an xarray.DataArray if mmap=False and a namedtuple
          with the same fields otherwise
        """
        import xarray as xr

        dataset_name = os.path.basename(location)
        if not dataset_name:
            raise ValueError(('Not a valid path {} inside hdf5 for loading '
                              'xarrays. Must be of the form '
                              '/<folder>/<array_name>.').format(location))
        if index and chunks:
            raise ValueError('index and chunks parameters cannot '
                             'be used together!')

        if mmap and (index or chunks):
            raise ValueError('mmap=True is not compatible with providing '
                             'index or chunks!')

        if backend not in ['pytables', 'h5py']:
            raise ValueError('unknown backend {}'.format(backend))

        fh = self.open('r', backend=backend)

        def _h5_loader(fh, location):
            if backend == 'pytables':
                location = ('root.' + location.strip('/')).replace('/', '.')

                return operator.attrgetter(location)(fh)
            elif backend == 'h5py':
                return fh[location]
            else:
                raise ValueError

        def _h5_attr_iter(x):
            if backend == 'pytables':
                return {key: getattr(x, key)
                        for key in [name for name in dir(x)
                                    if not name.startswith('_')]}.items()
            elif backend == 'h5py':
                return x.items()
            else:
                raise ValueError

        X_raw = _h5_loader(fh, location)

        if chunks:
            try:
                import dask.array as da
            except ImportError:
                raise ValueError('to use chunks parameter, dask needs to '
                                 ' be installed. Could not find dask!')
            X_raw = da.from_array(X_raw, chunks=chunks)
        elif index:
            X_raw = X_raw[index]
        elif not mmap:
            X_raw = X_raw[:]  # load data in memory
        scale_names = [el.decode('utf-8')
                       for el in _h5_loader(fh, location).attrs['scales']]

        coords = {}
        scale_units = {}

        for idx, name in enumerate(scale_names):
            coord_path = '/scales/' + '_'.join([dataset_name, name])
            coord_val = _h5_loader(fh, coord_path)
            if index:
                local_index = index[idx]
                coords[name] = coord_val[local_index]
            else:
                coords[name] = coord_val[:]

            scale_units[name] = coord_val.attrs['unit'].decode('utf-8')

        attrs = {'name': dataset_name,
                 'scale_units': scale_units}

        # save optional attributes
        for key, value in _h5_attr_iter(_h5_loader(fh, location).attrs):
            if key in ['name', 'scales']:
                continue
            if key.isupper():
                # skip system attributes in PyTables
                continue
            attrs[key] = value

        if not (chunks or mmap):
            fh.close()
            self._fh = None
        else:
            # create an attribute that we could close later if needed
            self._fh = fh

        if mmap:
            # xarray.DataArray does not support mmaps, so we
            # return a named tuple instead with the same fields
            nt = namedtuple('DataArrayMmap',
                            ('values', 'coords', 'dims', 'attrs', 'name'))
            return nt(X_raw, coords, tuple(scale_names), attrs, dataset_name)
        else:
            return xr.DataArray(X_raw, coords=coords, dims=scale_names,
                                attrs=attrs, name=dataset_name)
