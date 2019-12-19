# Transformer Unit Tests
This folder contains the docker image using unit tests [TravisCI](https://travis-ci.org/) will run in it's build.
These are basic functional unit tests, checks for output formatting and typing.
All tests are written in and utilizing [pytest](https://docs.pytest.org/en/latest/).
In addition to this, [pylint](https://www.pylint.org/) will also be deployed look here for our organization's [pylint protocols](https://github.com/AgPipeline/Organization-info).

### Testing Process
Upon submitting a pull request Travis will build and run the image automatically and will return a report with all passing or failing code.

### Running the tests before submitting a pull request
Should you wish to test your code before submitting a pull request follow these steps:
1) ```sh
    docker build -t common-image common-image
   ```
2) ```sh
    docker build -t test-image:latest test-image
   ```
3) ```sh
    docker run test-image
   ```

### Requirements 
There are no additional requirements or dependancies if not running these tests locally, if however these are to be run before deploying travis the following is required. 

[Docker](https://www.docker.com/)