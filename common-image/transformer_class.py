"""Class instance for Transformer
"""

import argparse
import configuration

class __internal__():
    """Class containing functions for this file only
    """
    def __init__(self):
        """Perform class level initialization
        """

class Transformer():
    """Generic class for supporting transformers
    """
    #pylint: disable=unused-argument
    def __init__(self, **kwargs):
        """Performs initialization of class instance
        Arguments:
            kwargs: additional parameters passed in to Transformer
        """
        self.sensor = None

    @property
    def default_epsg(self):
        """Returns the default EPSG code that utilities expect
        """
        return 4326

    @property
    def sensor_name(self):
        """Returns the name of the sensor we represent
        """
        return configuration.SENSOR_NAME

    def add_parameters(self, parser: argparse.ArgumentParser) -> None:
        """Adds processing parameters to existing parameters
        Arguments:
            parser: instance of argparse
        """
        parser.add_argument('--logging', '-l', nargs='?', default=os.getenv("LOGGING"),
                        help='file or url or logging configuration (default=None)')

    #pylint: disable=no-self-use
    def get_transformer_params(self, args: argparse.Namespace, metadata: dict) -> dict:
        """Returns a parameter list for processing data
        Arguments:
            args: result of calling argparse.parse_args
            metadata: the loaded metadata
        """
        # Setup logging
        setup_logging(args.logging)

        # Determine if we're using JSONLD (which we should be)
        if 'content' in metadata:
            parse_md = metadata['content']
        else:
            parse_md = metadata

        terraref_md = get_terraref_metadata(parse_md, configuration.TRANSFORMER_TYPE)
        if not terraref_md:
            return {'code': -5001, 'error': "Unable to load Gantry information from metadata for '%s'" % configuration.TRANSFORMER_TYPE}

        timestamp = __internal__.get_metadata_timestamp(terraref_md)
        if not timestamp:
            return {'code': -5002, 'error': "Unable to locate timestamp in metadata for '%s'" % configuration.TRANSFORMER_TYPE}

        # Fetch experiment name from terra metadata
        _, _, updated_experiment = do_get_season_and_experiment(timestamp, configuration.TRANSFORMER_TYPE, terraref_md)

        # Setup our sensor
        self.sensor = Sensor(base='', station='ua-mac', sensor=configuration.TRANSFORMER_SENSOR)
        leaf_name = self.sensor.get_display_name()

        # Get our trimmed metadata
        terraref_md_trim = get_terraref_metadata(parse_md)
        if updated_experiment is not None:
            terra_md_trim['experiment_metadata'] = updated_experiment

        # Prepare our parameters
        check_md = {'timestamp': timestamp,
                    'container_name': None,
                    'trigger_name': None,
                    'context_md': terraref_md_trim,
                    'working_folder': args.working_space,
                    'list_files': None
                   }

        return {'check_md': check_md,
                'transformer_md': get_extractor_metadata(terraref_md, configuration.TRANSFORMER_NAME),
                'full_md': parse_md
               }
