# Transformer: base RGB Plot-level

Provides the base image, or code, for plot-level RGB transformers for the UA Gantry Makeflow environment.

The motivation behind this code is to significantly reduce the overhead in knowledge and work needed to add scientific algorithms to the pipeline.

##  What's provided
The transformer creates output CSV files in single process, or multi-process environments.
If the output CSV files don't exist, they are created and initialized (the CSV header is written identifying the fields).
If the output CSV files already exist, rows are appended to the files.
No checks are made to determine if a particular entry already exists in the CSV files, data is just appended.

By default a generic CSV file is produced, as well as CSV files compatible with [TERRA REF Geostreams](https://docs.terraref.org/user-manual/data-products/environmental-conditions) and with [BETYDB](https://www.betydb.org/).

### Changing default CSV behavior
Algorithm writers have the ability to override this default behavior with TERRA REF Geostreams and BETYdb through the definition of variables in their implementation file.
* WRITE_GEOSTREAMS_CSV - if defined at the global level and set to `False` will suppress writing TERRA REF Geostreams CSV data for an algorithm.
* WRITE_BETYDB_CSV - if defined at the global level and set to `False` will suppress writing BETYdb CSV data for an algorithm.

In case people executing an algorithm wish to generate BETYdb or TERRA REF Geostreams CSV files, there are command line arguments that override the just mentioned global variable values to force writing. 
Of course, these command line arguments are not necessary if the files are being written by default.

### Output path
The `--csv_path` parameter is key to getting multiple instances of RGB plot-level transformers writing to the same file.
For each instance of the same transformer that's run (either single- or multi-process), using the same path indicates that the produced data should be appended to the CSV files (dependent upon runtime environments).
Of course, if the file doesn't already exist it's first created and the CSV header written before data is written.

If writing all the data to the same file isn't possible, or not desirable, this parameter can be modified to allow each instance to write its own file (including the CSV header).

Note: if using Docker images this path is relative to the code running inside the container.

