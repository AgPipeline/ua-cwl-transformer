"""Tests for transformer_class.py
"""

#Import transformer_class.py module and inmedded modules
import argparse
import os
from pyclowder.utils import setup_logging as pyc_setup_logging
import terrautils.lemnatec
from terrautils.metadata import get_terraref_metadata as tr_get_terraref_metadata, \
                                get_season_and_experiment as tr_get_season_and_experiment, \
                                get_extractor_metadata as tr_get_extractor_metadata
from terrautils.sensors import Sensors
import transformer_class
#import configuration

terrautils.lemnatec.SENSOR_METADATA_CACHE = os.path.dirname(os.path.realpath(__file__))

#Setting up testing classes
TEST_TRANSFORMER = transformer_class.Transformer()
TEST_INTERNAL = transformer_class.__internal__()
PARSE = argparse.Namespace()


# pylint:disable=import-error
# pylint:disable=unused-import
def test_get_metadata_timestamp():
    """Test for get_metadata_timestamp method within the __internal__ class
    """
    #Setup test param
    meta_data = {}

    #Saving method call to variable
    test_result = TEST_INTERNAL.get_metadata_timestamp(meta_data)

    #Should return str type
    assert isinstance(test_result, str)
    
def test_default_epsg():
    """Test for default_epsg method within the Transfomer class
    """

    #Saving method call to variable
    test_code = TEST_TRANSFORMER.default_epsg()
    
    #Method should only return an integer code: 4326
    assert test_code == 4326

def test_sensor_name():
    """Test for sensor_name method within the Transformer class
    """

    #Saving functon call to variable
    test_sensor = TEST_TRANSFORMER.sensor_name()

    #Should return str object
    assert isinstance(test_sensor, str)

def test_generate_transformer_md():
    """Test for generate_transformer_md method within the Transformer class
    """

    #Saving method call to variable
    test_md = TEST_TRANSFORMER.generate_transformer_md()

    #Should return dict type object
    assert isinstance(test_md, dict)

def test_add_parameters():
    """Test for the add_parameters method within the Transformer class
    """

    #Saving method call to variable
    test_add = TEST_TRANSFORMER.add_parameters(PARSE)

    #Should return None
    assert test_add is None

def test_get_transformer_params():
    """Test for the get_transformer_params method within the Transformer class
    """

    #Testing parameter for method call
    test_metadata = {}

    #Save method call to variable
    test_params = TEST_TRANSFORMER.get_transformer_params(PARSE, test_metadata)

    #Should return a dict type object
    assert isinstance(test_params, dict)
