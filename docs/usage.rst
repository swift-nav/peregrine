==================
Command-line Usage
==================

Peregrine can be used as a stand alone command-line tool for processing a
sample data file into a set of PVT solutions.

Usage information can be obtained by running::

  $ peregrine --help

At its most basic, peregrine can simply be passed the name of a sample data
file to process and it will perform acquisition, tracking and navigation
solution on the data file::

  $ peregrine path/to/sample_data_file

After each stage (acquisition, tracking and navigation solution), a 'results'
file is saved with the same name as the data file with the extensions
``.acq_results``, ``.track_results`` and ``.nav_results`` appended. These files
can be used for analysis at a later point or can be used to re-run peregrine,
skipping stages by loading their results from disk.

For example, to skip acquisition specify the ``-a`` option::

  $ peregrine -a sample_data_file

and peregrine will attempt to load the acquisition results from the file
``sample_data_file.acq_results`` and skip straight to tracking.

Similar options ``-t`` and ``-n`` exist for tracking and navigation respectively.

