Phicore data file format
========================

*Version: 2.0*, May 25 2018, LIDYL CEA

This document describes the API of the file format used to store spatio-temporal laser beam profiles.


I. HDF5 file format
-------------------

Overview
^^^^^^^^

Hierarchical Data Format (HDF5) is designed to efficiently store large amounts of scientific data.
A phicore data file, is an HDF5 file with the following structure,

.. code::
 
     |-metadata
     --data/
       |_ variable1  int16, shape=(Nx, Ny, Nw)
       |_ variable2  float32, shape=(Nx, Ny, Nt)
     --scales/
       |_ variable1_x float64, shape=(Nx,)
       |_ variable1_y float64, shape=(Ny,)
       |_ variable1_w float64, shape=(Nw,)
       |_ variable2_x float64, shape=(Nx)
       |_ variable2_y float64, shape=(Ny)
       |_ variable2_t float64, shape=(Nt)
        ...
     --diag/
       |_ reference_image1
       |_ reference_image2


Thus, phicore files always have at least the following three groups,

* **data** : a group with N-dimensional variables (in this case `variable1` and `variable2`)
* **scales** : contains 1D vectors with axis coordinates (time, space, etc) for all variables.
  in the above example, `variable1` is 3D and has `[x, y, w]` coordinates.
* **diag** : a group with custom variables. For instance it could contain reference images etc.

In addition, phicore files store metadata as specified below.

Data variables
^^^^^^^^^^^^^^

Data variables in the ``data/`` group can be 2D or 3D array of integer or float data type.

Spatial dimensions are the first ones, while the temporal or frequency dimension comes last.

To save disk usage, individual variables can be stored with
`compression filters <https://support.hdfgroup.org/HDF5/faq/compression.html>`_ including zlib, szip as
well as blosc and lz4.

Metadata
^^^^^^^^

**Root metadata**

The root HDF5 node node must contain at least the following metadata attributes,

  *  ``rev_fileformat`` (_float_): File format revision. Should be equal to ``3``.
  *  ``date`` (_string_): "YYYY-MM-DD-HHMMSS"

as well as the following optional attributes,

  *  ``operator`` (_string_): Author name
  *  ``comments`` (_string_): Free format field.
  *  ``data_source`` (_string_): "simulation" OR "experiment"

other attributes can be added as needed.

Node metadata
^^^^^^^^^^^^^

Each data variable must store the following metadata attributes,

  * ``name`` (_string_): the variable name
  * ``scales`` (_string_): a list of data coordinates (e.g. ``['x', 'y', 'w']``)
  
as well as the following optional attributes,

  * ``data_source`` (_string_): "simulation" OR "experiment"

Each scale/coordinate variable must include the following attributes,
  * ``unit`` (_string_): a string representation of coordinate unit


Physical quantities
^^^^^^^^^^^^^^^^^^^

**Data variable notations**

The variable names are Intensity (``I``), Amplitude (``A``), Complex electric field (``E``) and Phase (``ph``).

**Coordinate notations**

=======================    ================   ========
Description                Name               Units   
=======================    ================   ========                                          
Spatial coordinates        ``x`` or ``y``     mm       
Spatial frequencies        ``kx`` or ``ky``   1/mm     
Time                       ``t``              fs       
Optical delay              ``tau``            fs       
Optical path difference    ``d``              nm       
Angular frequency          ``w``              PHz.rad  
Frequency                  ``f``              PHz      
Wavelength                 ``lamb``           nm       
=======================    ================   ======== 

Visualization software
^^^^^^^^^^^^^^^^^^^^^^

Visualization software for the phicore data format is developed at LIDYL, CEA. 

Raw data in the HDF5 can be displayed by a variety of HDF5 viewers, including
`HDF Compass <https://github.com/HDFGroup/hdf-compass>`_,
`HDF view <https://www.hdfgroup.org/downloads/hdfview/>`_ and
`ViTabes <http://vitables.org/>`_.


II. Client libraries
--------------------

HDF5 supports client libraries in numerous languages, including Java, MATLAB, Scilab, Octave,
Mathematica, IDL, Python, R, and Julia however the phicore data format specification for each of these
still needs to be implemented.

In the following, we will focus on the Python language.

Python
^^^^^^

**Overview**
A client library for the phicore data format is implemented at LIDYL, CEA and is available upon request.

The general approach consists in mapping the HDF5 file structure to labeled N-dimensional array representation
provided by the `xarray <http://xarray.pydata.org/en/stable/index.html>`_ package. 

Each data variable can be represented as an
`xarray.DataArray <http://xarray.pydata.org/en/stable/generated/xarray.DataArray.html>`_, while the set of all
data variables corresponds to  `xarray.Dataset <http://xarray.pydata.org/en/stable/generated/xarray.Dataset.html>`_.

**Specification**

Each data variable ``X`` must be a valid 2D or 3D xarray object
(see `xarray API <http://xarray.pydata.org/en/stable/data-structures.html#dataarray>`_) and include the following attributes,

 * ``scale_units`` *(dict)*: a dictionary mapping dimensions names (``X.dims``) to their units types (str).

As a result of the "Physical quantities" section, ``X.dim`` must be of the form [``x|kx``, ``y|ky``, ``lamb|w|f|tau|d``], while
``X.coords`` must be a dict-like object with these same keys.

**Example**

A data variable ``X`` represented as an ``xarray.DataArray`` can be saved to disk with,


.. code::python


    from phicore.io import PhiDataFile

    fh = PhiDataFile('example_file.h5', 'w')
    fh.write_xarray(X)
    ```
    then read with
    ```py
    fh = PhiDataFile('example_file.h5', 'r')
    X = fh.read_xarray("/data/X")
