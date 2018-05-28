import os
import time
import warnings

import h5py
import tables as tb
import xarray as xr

__fileformatversion__ = 2

warnings.simplefilter('always', DeprecationWarning)


class PhiDataFile(object):
    def __init__(self, fullpath, mode="r", force=False):
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
                             .format(self.mode))
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

    def open(self, mode=None, backend='h5py', filters=None):
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
            return h5py.File(self.fullpath, mode)
        elif backend == 'pytables':
            return tb.open_file(self.fullpath, mode=mode, filters=filters)
        else:
            raise ValueError("Wrong backend {}".format(backend))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def _create_file(self):
        """Initialize basic file structure"""
        with h5py.File(self.fullpath, 'w') as f:
            f.create_group('data')
            f.create_group('scales')
            f.create_group('diag')
            f.attrs['rev_fileformat'] = __fileformatversion__

    def create_group(self, name, location=None):
        """ Create a new dataset see h5py.Group.create_group """
        with self.open('a') as fh:
            if location is None:
                out = fh.create_group(name)
            else:
                out = fh[location].create_group(name)
        return out

    def create_dataset(self, name, data, fletcher32=True, complib='blosc:lz4',
                       complevel=0, chunks=None, backend='pytables', **args):
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

    def write_attrs(self, attrs, location=None):
        """ Write attributes to a h5 node

        Parameters
        ----------
        location : str
          location path inside the hdf5

        data : xarray.DataArray
          the data to save
        """

        with self.open('a') as fh:
            if location is None:
                fh_attrs = fh.attrs
            else:
                fh_attrs = fh[location].attrs

            for key, val in attrs.items():
                fh_attrs[key] = val

    def get_attrs(self, location=None):
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

    def list_xarray(self, location='/data/'):
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

    def write_xarray(self, data, location='/data/', chunks=None,
                     backend='pytables', complib="blosc:lz4",
                     complevel=0, **args):
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
        self.create_dataset(location, data=data.values, chunks=chunks,
                            backend=backend, complib=complib,
                            complevel=complevel, **args)
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
                fh[location].attrs[key] = value

    def read_xarray(self, location, index=(), chunks=()):
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
        """
        dataset_name = os.path.basename(location)
        if not dataset_name:
            raise ValueError(('Not a valid path {} inside hdf5 for loading '
                              'xarrays. Must be of the form '
                              '/<folder>/<array_name>.').format(location))
        if index and chunks:
            raise ValueError('index and chunks parameters cannot '
                             'be used together!')

        fh = self.open('r')

        X_raw = fh[location]
        if chunks:
            try:
                import dask.array as da
            except ImportError:
                raise ValueError('to use chunks parameter, dask needs to '
                                 ' be installed. Could not find dask!')
            X_raw = da.from_array(X_raw, chunks=chunks)
        elif index:
            X_raw = X_raw[index]
        else:
            X_raw = X_raw[:]  # load data in memory
        scale_names = [el.decode('utf-8')
                       for el in fh[location].attrs['scales']]

        coords = {}
        scale_units = {}

        for idx, name in enumerate(scale_names):
            coord_path = '/scales/' + '_'.join([dataset_name, name])
            coord_val = fh[coord_path]
            if index:
                local_index = index[idx]
                coords[name] = coord_val[local_index]
            else:
                coords[name] = coord_val[:]

            scale_units[name] = coord_val.attrs['unit'].decode('utf-8')

        attrs = {'name': dataset_name,
                 'scale_units': scale_units}

        # save optional attributes
        for key, value in fh[location].attrs.items():
            if key in ['name', 'scales']:
                continue
            if key.isupper():
                # skip system attributes in PyTables
                continue
            attrs[key] = fh[location].attrs[key]

        if not chunks:
            fh.close()

        return xr.DataArray(X_raw, coords=coords, dims=scale_names,
                            attrs=attrs, name=dataset_name)
