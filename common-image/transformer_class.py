"""Class instance for Transformer
"""

import os
import argparse

from pyclowder.utils import setup_logging as pyc_setup_logging
from terrautils.metadata import get_terraref_metadata as tr_get_terraref_metadata, \
                                get_season_and_experiment as tr_get_season_and_experiment, \
                                get_extractor_metadata as tr_get_extractor_metadata
from terrautils.sensors import Sensors
from terrautils.imagefile import get_epsg as tr_get_epsg, \
                                 image_get_geobounds as tr_image_get_geobounds
import terrautils.lemnatec

import configuration

terrautils.lemnatec.SENSOR_METADATA_CACHE = os.path.dirname(os.path.realpath(__file__))

class __internal__():
    """Class containing functions for this file only
    """
    def __init__(self):
        """Perform class level initialization
        """

    @staticmethod
    def get_metadata_timestamp(metadata: dict) -> str:
        """Looks up the timestamp in the metadata
        Arguments:
            metadata: the metadata to find the timestamp in
        """
        if 'content' in metadata:
            check_md = metadata['content']
        else:
            check_md = metadata

        timestamp = None
        if 'timestamp' in check_md:
            timestamp = check_md['timestamp']
        elif 'gantry_variable_metadata' in check_md:
            if 'datetime' in check_md['gantry_variable_metadata']:
                timestamp = check_md['gantry_variable_metadata']['datetime']

        return timestamp

class Transformer():
    """Generic class for supporting transformers
    """
    def __init__(self, **kwargs):
        """Performs initialization of class instance
        Arguments:
            kwargs: additional parameters passed in to Transformer
        """
        # pylint: disable=unused-argument
        self.sensor = None
        self.args = None

    @property
    def default_epsg(self):
        """Returns the default EPSG code that utilities expect
        """
        return 4326

    @property
    def sensor_name(self):
        """Returns the name of the sensor we represent
        """
        return configuration.TRANSFORMER_SENSOR

    @property
    def supported_image_file_exts(self):
        """Returns the list of supported image file extension strings (in lower case)
        """
        return ['tif', 'tiff', 'jpg']

    def get_image_file_epsg(self, source_path: str) -> str:
        """Returns the EPSG of the georeferenced image file
        Arguments:
            source_path: the path to the image to load the EPSG code from
        Return:
            Returns the EPSG code loaded from the file. None is returned if there is a problem or the file
            doesn't have an EPSG code
        """
        # pylint: disable=no-self-use
        return tr_get_epsg(source_path)

    def get_image_file_geobounds(self, source_path: str) -> list:
        """Uses gdal functionality to retrieve rectilinear boundaries from the file
        Args:
            source_path(str): path of the file to get the boundaries from
        Returns:
            The upper-left and calculated lower-right boundaries of the image in a list upon success.
            The values are returned in following order: min_y, max_y, min_x, max_x. A list of numpy.nan
            is returned if the boundaries can't be determined
        """
        # pylint: disable=no-self-use
        return tr_image_get_geobounds(source_path)

    def generate_transformer_md(self) -> dict:
        """Generates metadata about this transformer
        Returns:
            Returns the transformer metadata
        """
        # pylint: disable=no-self-use
        return {
            'version': configuration.TRANSFORMER_VERSION,
            'name': configuration.TRANSFORMER_NAME,
            'author': configuration.AUTHOR_NAME,
            'description': configuration.TRANSFORMER_DESCRIPTION,
            'repository': {'repUrl': configuration.REPOSITORY}
        }

    def add_parameters(self, parser: argparse.ArgumentParser) -> None:
        """Adds processing parameters to existing parameters
        Arguments:
            parser: instance of argparse
        """
        # pylint: disable=no-self-use
        parser.add_argument('--logging', '-l', nargs='?', default=os.getenv("LOGGING"),
                            help='file or url or logging configuration (default=None)')

        parser.epilog = configuration.TRANSFORMER_NAME + ' version ' + configuration.TRANSFORMER_VERSION + \
                        ' author ' + configuration.AUTHOR_NAME + ' ' + configuration.AUTHOR_EMAIL

    def get_transformer_params(self, args: argparse.Namespace, metadata: dict) -> dict:
        """Returns a parameter list for processing data
        Arguments:
            args: result of calling argparse.parse_args
            metadata: the loaded metadata
        """
        # pylint: disable=no-self-use
        # Setup logging
        pyc_setup_logging(args.logging)

        self.args = args

        # Determine if we're using JSONLD (which we should be)
        if 'content' in metadata:
            parse_md = metadata['content']
        else:
            parse_md = metadata

        terraref_md = tr_get_terraref_metadata(parse_md, configuration.TRANSFORMER_SENSOR)
        if not terraref_md:
            return {'code': -5001, 'error': "Unable to load Gantry information from metadata for '%s'" % \
                                                                                    configuration.TRANSFORMER_TYPE}

        timestamp = __internal__.get_metadata_timestamp(parse_md)
        if not timestamp:
            return {'code': -5002, 'error': "Unable to locate timestamp in metadata for '%s'" % \
                                                                                    configuration.TRANSFORMER_TYPE}

        # Fetch experiment name from terra metadata
        season_name, experiment_name, updated_experiment = \
                                    tr_get_season_and_experiment(timestamp, configuration.TRANSFORMER_TYPE, terraref_md)

        # Setup our sensor
        self.sensor = Sensors(base='', station='ua-mac', sensor=configuration.TRANSFORMER_SENSOR)
        leaf_name = self.sensor.get_display_name()

        # Get our trimmed metadata
        terraref_md_trim = tr_get_terraref_metadata(parse_md)
        if updated_experiment is not None:
            terraref_md_trim['experiment_metadata'] = updated_experiment

        # Get the list of files, if there are some
        file_list = []
        if args.file_list:
            for one_file in args.file_list:
                # Filter out arguments that are obviously not files
                if not one_file.startswith('-'):
                    file_list.append(one_file)

        # Prepare our parameters
        check_md = {'timestamp': timestamp,
                    'season': season_name,
                    'experiment': experiment_name,
                    'container_name': None,
                    'target_container_name': leaf_name, # TODO: Is this needed?
                    'trigger_name': None,
                    'context_md': terraref_md_trim,
                    'working_folder': args.working_space,
                    'list_files': lambda: file_list
                   }

        return {'check_md': check_md,
                'transformer_md': tr_get_extractor_metadata(terraref_md, configuration.TRANSFORMER_NAME),
                'full_md': parse_md
               }
