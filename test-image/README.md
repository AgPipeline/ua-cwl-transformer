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

## Docker Image Notes
This section contains information on the Dockerfile and some build notes.

### What's Provided
Be sure to check the [Dockerfile](https://github.com/AgPipeline/ua-gantry-transformer/blob/common-extractor/common-image/Dockerfile) for an exact list of what's installed.

The Python packages of `numpy` and `gdal` are installed to allow array manipulation and geo-spatial support.

### Build Arguments
There are Docker build arguments defined in the Dockerfile.
These are intended to provide additional flexibility for installing packages when building a Docker image, without having to edit the Dockerfile.
