# Common Image
This folder contains the base files for the [Gantry workflow at UA](https://github.com/AgPipeline/Organization-info) environment.
This environment builds off this organizations [base docker support](https://github.com/AgPipeline/base-docker-support), replacing the *transformer_class.py* file.
Please refer to that repo for additional context.

## Purpose
As part of providing an environment suitable for the Gantry workflow at UA, there are additional variables defined in the [configuration.py](https://github.com/AgPipeline/ua-gantry-transformer/blob/common-extractor/common-image/configuration.py) file.

Our [transformer_class.Transformer](https://github.com/AgPipeline/ua-gantry-transformer/blob/common-extractor/common-image/transformer_class.py) instance adds to the  command line parameters.
Additionally, the metadata that's received is processed to make it easier for transformers to perform their work.
It's expected that common functions will be added to our Transformer class as additional TERRA REF extractors get ported to the new framework.

## Relation to Finished Transformers
Now that an environment has been provided through this code, a transformer template needs to be cloned and developed.
In most cases the result of cloning the developing the transformer template will provide a final product.

### Named Parameters
The named parameters provided to transformers are:
- check_md: contains request specific information
- transformer_md: contains a list of metadata specific to a transformer that was pulled from the overall request metadata
- full_md: the full set of metadata for the current request.

#### check_md
This parameter is a dict and contains request specific information.
- timestamp: the timestamp associated with this request (pulled from the metadata)
- season: the name of the season (pulled from the metadata)
- experiment: the name of the experiment (pulled from the metadata)
- container_name: the name of the source container when specified
- target_container_name: name generated from the configured sensor information
- trigger_name: name of what triggered the current request
- context_md: the gantry metadata and sensor specific fixed metadata
- working_folder: the location of the working folder
- list_files: a function that returns the list of relevent files for this request

### transformer_md
Contains any transformer specific metadata as set by previous runs of the transformer.
The transformer name is used to determine relevent metadata.

#### full_md
The full set of metadata for this request.
If the metadata was in JSONLD format, this parameter will contain the content and not the full JSON.

## Docker Image Notes
This section contains information on the Dockerfile and some build notes.

### What's Provided
Be sure to check the [Dockerfile](https://github.com/AgPipeline/ua-gantry-transformer/blob/common-extractor/common-image/Dockerfile) for an exact list of what's installed.

The Python packages of `numpy` and `gdal` are installed to allow array manipulation and geo-spatial support.

### Build Arguments
There are Docker build arguments defined in the Dockerfile.
These are intended to provide additional flexibility for installing packages when building a Docker image, without having to edit the Dockerfile.
