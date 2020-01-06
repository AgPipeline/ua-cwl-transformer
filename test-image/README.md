# Test Image
This folder contains the base files for the common image ua gantry environment.
This environment builds off this organizations [base docker support](https://github.com/AgPipeline/base-docker-support), replacing the *transformer_class.py* file.
Please refer to that repo for additional context.

## Purpose
This image holds the unit tests [TravisCI](https://travis-ci.org/) will run in it's build. 
These are basic functional unit tests, checks for output formatting and typing. 
All tests are written in and utilizing [pytest](https://docs.pytest.org/en/latest/). 
In addition to this, [pylint](https://www.pylint.org/) will also be deployed. 
Look into our organization's repository for our [pylint protocols](https://github.com/AgPipeline/Organization-info).

### Running the tests
Upon submitting a pull request Travis will build and run the testing modules automatically and return a report with passing and failing code. 

### Running the tests before submitting a pull request
Should you wish to test your code before submitting a pull request follow these steps:
1) Clone, pull, copy or otherwise aquire the pylintrc file located at this [repo](https://github.com/AgPipeline/Organization-info)
2) From the command line run the following commands (from common-image as current directory)
    ```sh
    pylint --rcfile=<path-to-pylint.rc> *py
    pylint --rcfile=<path-to-pylint.rc> /**/*.py
    ```
3) Once the previous commands have executed there will be a list of changes that should be made to bring any code up to standard
4) From the command line run the following command while the current working directory is still ua-gantry-transormer
    ```sh
    cp common-image/*.py test-image/
    docker build -t test-image:latest test-image
    docker run test-image
    ```

### Requirements 
Only docker is required to run the tests since the dockerfile will handle everything else.

### What's Provided
Be sure to check the [Dockerfile](https://github.com/AgPipeline/ua-gantry-environment/blob/test-development/test-image/Dockerfile) for an exact list of what's installed.

The Python packages of `numpy` and `gdal` are installed to allow array manipulation and geo-spatial support.

### Build Arguments
There are Docker build arguments defined in the Dockerfile.
These are intended to provide additional flexibility for installing packages when building a Docker image, without having to edit the Dockerfile.
