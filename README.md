# University of Arizona Transformer for Common Workflow Language
This repo contains source for building base docker images for the University of Arizona (UA) environment that uses Common Workflow Language (CWL) for processing Gantry data.

The images built here are from the AgPipeline image(s) created by the [base docker support](https://github.com/AgPipeline/base-docker-support) repo.

## Details
The transformer_class.py file in the base images are replaced by our version which provides the correct environment for derived transformers.

The command line arguments are saved in the `args` variable of the class instance.

## How to Contribute
If the current images don't provide the functionality needed, please put in a [feature request](https://github.com/AgPipeline/computing-pipeline/issues/new/choose) before creating a new image.
Your feedback is important to us and it's quite possible that we will want to incorporate your request in our existing images.

If you need a separate environment, such as for the CyVerse Discovery Environment (DE), please consider using a separate repo for your work (within this organization is a good place).
If you are creating an environment *derived* from this one, you might also want to consider a separate repo for your work.

If you are creating a new folder for a new image, please use a meaningful prefix to the folder name; for example, use a prefix of 'gdal' for an image that has gdal pre-installed.

Also, be sure to read about how to [contribute](https://github.com/AgPipeline/Organization-info) to this organization.

## Testing 
The testing modules and readme can be found in the [testing image](https://github.com/AgPipeline/ua-gantry-environment/tree/test-development/test-image)
