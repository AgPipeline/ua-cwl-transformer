"""Base of plot-level Lidar transformer
"""

import argparse
import copy
import datetime
import json
import liblas
import logging
import math
import numpy as np
import os
from osgeo import ogr
import osr
import random
import re
import subprocess
import time
from typing import Optional
import yaml



import algorithm_lidar
import configuration
import transformer_class

# Number of tries to open a CSV file before we give up
MAX_CSV_FILE_OPEN_TRIES = 10

# Maximum number of seconds a single wait for file open can take
MAX_FILE_OPEN_SLEEP_SEC = 30

# Array of trait names that should have array values associated with them
TRAIT_NAME_ARRAY_VALUE = ['canopy_cover', 'site']

# Mapping of default trait names to fixed values
TRAIT_NAME_MAP = {
    'local_datetime': None,
    'access_level': '2',
    'species': 'Unknown',
    'site': '',
    'citation_author': '"Unknown"',
    'citation_year': '0000',
    'citation_title': 'Unknown',
    'method': 'Unknown'
}

# Trait names arrays
CSV_TRAIT_NAMES = ['germplasmName', 'site', 'timestamp', 'lat', 'lon', 'citation_author', 'citation_year', 'citation_title']
GEO_TRAIT_NAMES = ['site', 'trait', 'lat', 'lon', 'dp_time', 'source', 'value', 'timestamp']
BETYDB_TRAIT_NAMES = ['local_datetime', 'access_level', 'species', 'site', 'citation_author', 'citation_year', 'citation_title',
                      'method']

# Used to generate random numbers
RANDOM_GENERATOR = None

# The LAT-LON EPSG code to use
LAT_LON_EPSG_CODE = 4326

# Names of files generated
FILE_NAME_CSV = "lidar_plot.csv"
FILE_NAME_GEO_CSV = "lidar_plot_geo.csv"
FILE_NAME_BETYDB_CSV = "lidar_plot_betydb.csv"

class __internal__():
    """Class containing functions for this file only
    """
    # pylint: disable=too-many-public-methods
    def __init__(self):
        """Perform class level initialization
        """

    @staticmethod
    def get_algorithm_definition_bool(variable_name: str, default_value: bool = False) -> bool:
        """Returns the value of the algorithm definition as a boolean value
        Arguments:
            variable_name: the name of the variable to look up
            default_value: the default value to return if the variable is not defined or is None
        """
        value = False
        if hasattr(algorithm_lidar, variable_name):
            temp_name = getattr(algorithm_lidar, variable_name)
            if temp_name:
                value = True
            elif temp_name is not None:
                value = False

        return value if value else default_value

    @staticmethod
    def get_algorithm_definition_str(variable_name: str, default_value: str = '') -> str:
        """Returns the value of the string variable found in algorithm_lidar
        Arguments:
            variable_name: the name of the definition to find
            default_value: the default value to return if the variable isn't defined, is not a string, or has an empty value
        Notes:
            If the variable can't be determined, the default value is returned
        """
        value = None
        if hasattr(algorithm_lidar, variable_name):
            temp_name = getattr(algorithm_lidar, variable_name)
            if isinstance(temp_name, str):
                value = temp_name.strip()

        return value if value else default_value

    @staticmethod
    def get_algorithm_name() -> str:
        """Convenience function for returning the name of the algorithm
        """
        return __internal__.get_algorithm_definition_str('ALGORITHM_NAME', 'unknown algorithm')

    @staticmethod
    def get_algorithm_variable_list(definition_name: str) -> list:
        """Returns a list containing the variable information defined by the algorithm
        Arguments:
            definition_name: name of the variable definition to look up
        Return:
            A list of variable strings
        Note:
            Assumes that multiple variable-related strings are comma separated
        """
        if not hasattr(algorithm_lidar, definition_name):
            raise RuntimeError("Unable to find %s defined in algorithm_lidar code" % definition_name)

        names = getattr(algorithm_lidar, definition_name).strip()
        if not names:
            raise RuntimeError("Empty %s definition specified in algorithm_lidar code" % definition_name)

        return names.split(',')

    @staticmethod
    def get_algorithm_variable_labels() -> list:
        """Returns a list containing all the variable names defined by the algorithm
        Return:
            A list of variable names
        """
        return_labels = []
        if hasattr(algorithm_lidar, 'VARIABLE_LABELS'):
            labels = getattr(algorithm_lidar, 'VARIABLE_LABELS').strip()
            if labels:
                return_labels = labels.split(',')

        return return_labels

    @staticmethod
    def recursive_metadata_search(metadata_list: list, search_key: str, special_key: str = None) -> str:
        """Performs a depth-first search for the key in the metadata and returns the found value
        Arguments:
            metadata_list: the metadata in which to look
            search_key: the key to look for in the metadata
            special_key: optional special key to look up the key under. If specified and found, the found value takes precedence
        Return:
            Returns the found key value, or an empty string
        Notes:
            The metadata is searched recursively for the key. If a key is found under the special key, it will be
            returned regardless of whether there's a key found elsewhere in the metadata
        """
        top_found_name = None
        return_found_name = ''
        for metadata in metadata_list:
            for key in metadata:
                if key == search_key:
                    top_found_name = metadata[key]
                if special_key and key == special_key:
                    if isinstance(metadata[key], dict):
                        temp_found_name = __internal__.recursive_metadata_search([metadata[key]], search_key, special_key)
                        if temp_found_name:
                            return_found_name = str(temp_found_name)
                            break
                elif isinstance(metadata[key], dict):
                    temp_found_name = __internal__.recursive_metadata_search([metadata[key]], search_key, special_key)
                    if temp_found_name:
                        top_found_name = str(temp_found_name)

        return top_found_name if top_found_name is not None else return_found_name

    @staticmethod
    def find_metadata_value(metadata_list: list, key_terms: list) -> str:
        """Returns the first found value associated with a key
        Arguments:
            metadata_list: the metadata to search
            key_terms: the keys to look for
        Returns:
            Returns the found value or an empty string
        """
        for one_key in key_terms:
            value = __internal__.recursive_metadata_search(metadata_list, one_key)
            if value:
                return value

        return ''

    @staticmethod
    def prepare_algorithm_metadata() -> tuple:
        """Prepares metadata with algorithm information
        Return:
            Returns a tuple with the name of the algorithm and a dictionary with information on the algorithm
        """
        return (__internal__.get_algorithm_definition_str('ALGORITHM_NAME', 'unknown'),
               {
                    'version': __internal__.get_algorithm_definition_str('VERSION', 'x.y'),
                    'traits': __internal__.get_algorithm_definition_str('VARIABLE_NAMES', ''),
                    'units': __internal__.get_algorithm_definition_str('VARIABLE_UNITS', ''),
                    'labels': __internal__.get_algorithm_definition_str('VARIABLE_LABELS', '')
               })


    @staticmethod
    def get_las_epsg_from_header(header: liblas.header.Header) -> str:
        """Returns the found EPSG code from the LAS header
        Arguments:
            header: the loaded LAS header to find the SRID in
        Return:
            Returns the SRID as a string if found, None is returned otherwise
        """
        epsg = None
        search_terms_ordered = ['DATUM', 'AUTHORITY', '"EPSG"', ',']
        try:
            # Get the WKT from the header, find the DATUM, then finally the EPSG code
            srs = header.get_srs()
            wkt = srs.get_wkt().decode('UTF-8')
            idx = -1
            for term in search_terms_ordered:
                idx = wkt.find(term)
                if idx < 0:
                    break
            if idx >= 0:
                epsg = re.search(r'\d+', wkt[idx:])[0]
        except Exception as ex:
            logging.debug("Unable to find EPSG in LAS file header")
            logging.debug("    exception caught: %s", str(ex))

        return epsg

    @staticmethod
    def get_las_extents(file_path: str, default_epsg: int = None) -> Optional[str]:
        """Calculate the extent of the given las file and return as GeoJSON.
        Arguments:
            file_path: path to the file from which to load the bounds
            default_epsg: the default EPSG to assume if a file has a boundary but not a coordinate system
        Return:
            Returns the JSON representing the image boundary, or None if the
            bounds could not be loaded
        Notes:
            If a file doesn't have a coordinate system and a default epsg is specified, the
            return JSON will use the default_epsg.
            If a file doesn't have a coordinate system and there isn't a default epsg specified, the boundary
            of the image is not returned (None) and a warning is logged.
        """
        # Get the bounds and the EPSG code
        las_info = liblas.file.File(file_path, mode='r')
        min_bound = las_info.header.min
        max_bound = las_info.header.max
        epsg = __internal__.get_las_epsg_from_header(las_info.header)
        if epsg is None:
            if default_epsg is not None:
                epsg = default_epsg
            else:
                logging.warning("Unable to find EPSG and not default is specified for file '%s'", file_path)
                return None

        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(min_bound[1], min_bound[0])  # Upper left
        ring.AddPoint(min_bound[1], max_bound[0])  # Upper right
        ring.AddPoint(max_bound[1], max_bound[0])  # lower right
        ring.AddPoint(max_bound[1], min_bound[0])  # lower left
        ring.AddPoint(min_bound[1], min_bound[0])  # Closing the polygon

        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)

        ref_sys = osr.SpatialReference()
        if ref_sys.ImportFromEPSG(int(epsg)) == ogr.OGRERR_NONE:
            poly.AssignSpatialReference(ref_sys)
            return geometry_to_geojson(poly)

        logging.error("Failed to import EPSG %s for las file %s", str(epsg), file_path)
        return None

    @staticmethod
    def clip_las(las_path: str, clip_tuple: tuple, out_path: str) -> None:
        """Clip LAS file to polygon.
        Arguments:
          las_path: path to point cloud file
          clip_tuple: tuple containing (minX, maxX, minY, maxY) of clip bounds
          out_path: output file to write
        Notes:
            The clip_tuple is assumed to be in the correct coordinate system for the point cloud file
        """
        bounds_str = "([%s, %s], [%s, %s])" % (clip_tuple[0], clip_tuple[1], clip_tuple[2], clip_tuple[3])

        pdal_dtm = out_path.replace(".las", "_dtm.json")
        with open(pdal_dtm, 'w') as dtm:
            dtm_data = """{
                "pipeline": [
                    "%s",
                    {
                        "type": "filters.crop",
                        "bounds": "%s"
                    },
                    {
                        "type": "writers.las",
                        "filename": "%s"
                    }
                ]
            }""" % (las_path, bounds_str, out_path)
            logging.debug("Writing dtm file contents: %s", str(dtm_data))
            dtm.write(dtm_data)

        cmd = 'pdal pipeline "%s"' % pdal_dtm
        logging.debug("Running pipeline command: %s", cmd)
        subprocess.call([cmd], shell=True)
        os.remove(pdal_dtm)

    @staticmethod
    def get_time_stamps(iso_timestamp: str) -> list:
        """Returns the date and the local time (offset is stripped) derived from the passed in timestamp
        Return:
            A list consisting of the date (YYYY-MM-DD) and a local timestamp (YYYY-MM-DDTHH:MM:SS)
        """
        # Strip the offset from the string
        time_date_sep = iso_timestamp.find('T')
        time_offset_sep = iso_timestamp.rfind('-')
        if 0 <= time_date_sep < time_offset_sep:
            # We have a time offset
            working_timestamp = iso_timestamp[: time_offset_sep]
        else:
            working_timestamp = iso_timestamp

        timestamp = datetime.datetime.strptime(working_timestamp, "%Y-%m-%dT%H:%M:%S")

        return [timestamp.strftime('%Y-%m-%d'), timestamp.strftime('%Y-%m-%dT%H:%M:%S')]

    @staticmethod
    def get_open_backoff(prev: float = None) -> float:
        """Returns the number of seconds to back off from opening a file
        Args:
            prev(int or float): the previous return value from this function
        Return:
            Returns the number of seconds (including fractional seconds) to wait
        Note that the return value is deterministic, and always the same, when None is
        passed in
        """
        # pylint: disable=global-statement
        global RANDOM_GENERATOR
        global MAX_FILE_OPEN_SLEEP_SEC

        # Simple case
        if prev is None:
            return 1

        # Get a random number generator
        if RANDOM_GENERATOR is None:
            try:
                RANDOM_GENERATOR = random.SystemRandom()
            finally:
                # Set this so we don't try again
                RANDOM_GENERATOR = 0

        # Get a random number
        if RANDOM_GENERATOR:
            multiplier = RANDOM_GENERATOR.random()  # pylint: disable=no-member
        else:
            multiplier = random.random()

        # Calculate how long to sleep
        sleep = math.trunc(float(prev) * multiplier * 100) / 10.0
        if sleep > MAX_FILE_OPEN_SLEEP_SEC:
            sleep = max(0.1, math.trunc(multiplier * 100) / 10)

        return sleep

    @staticmethod
    def write_csv_file(filename, header, data):
        """Attempts to write out the data to the specified file. Will write the
           header information if it's the first call to write to the file.
           If the file is not available, it waits as configured until it becomes
           available, or returns an error.
           Args:
                filename(str): path to the file to write to
                header(str): Optional CSV formatted header to write to the file; can be set to None
                data(str): CSV formatted data to write to the file
            Return:
                Returns True if the file was written to and False otherwise
        """
        # pylint: disable=global-statement
        global MAX_CSV_FILE_OPEN_TRIES

        if not filename or not data:
            logging.error("Empty parameter passed to write_geo_csv")
            return False

        csv_file = None
        backoff_secs = None
        for tries in range(0, MAX_CSV_FILE_OPEN_TRIES):
            try:
                csv_file = open(filename, 'a+')
            except Exception as ex:
                # Ignore an exception here since we handle it below
                logging.exception("Exception caught while trying to open CSV file: %s", filename)

            if csv_file:
                break

            # If we can't open the file, back off and try again (unless it's our last try)
            if tries < MAX_CSV_FILE_OPEN_TRIES - 1:
                backoff_secs = __internal__.get_open_backoff(backoff_secs)
                logging.info("Sleeping for %s seconds before trying to open CSV file again", str(backoff_secs))
                time.sleep(backoff_secs)

        if not csv_file:
            logging.error("Unable to open CSV file for writing: '%s'", filename)
            return False

        wrote_file = False
        try:
            # Check if we need to write a header
            if os.fstat(csv_file.fileno()).st_size <= 0:
                csv_file.write(header + "\n")

            # Write out data
            csv_file.write(data + "\n")

            wrote_file = True
        except Exception as ex:
            logging.exception("Exception while writing CSV file: '%s'", filename)
            # Re-raise the exception
            raise ex from None
        finally:
            csv_file.close()

        # Return whether or not we wrote to the file
        return wrote_file

    @staticmethod
    def get_csv_fields(variable_names: list) -> list:
        """Returns the list of CSV field names as a list
        Arguments:
            variable_names: a list of trait variable names to add to the returned list
        """
        return CSV_TRAIT_NAMES + list(variable_names)

    @staticmethod
    def get_geo_fields() -> list:
        """Returns the supported field names as a list
        """
        return GEO_TRAIT_NAMES

    @staticmethod
    def get_bety_fields(variable_names: list) -> list:
        """Returns the supported field names as a list
        Arguments:
            variable_names: a list of trait variable names to add to the returned list
        """
        return BETYDB_TRAIT_NAMES + list(variable_names)

    @staticmethod
    def get_default_trait(trait_name):
        """Returns the default value for the trait name
        Args:
           trait_name(str): the name of the trait to return the default value for
        Return:
            If the default value for a trait is configured, that value is returned. Otherwise
            an empty string is returned.
        """
        # pylint: disable=global-statement
        global TRAIT_NAME_ARRAY_VALUE
        global TRAIT_NAME_MAP

        if trait_name in TRAIT_NAME_ARRAY_VALUE:
            return []  # Return an empty list when the name matches
        if trait_name in TRAIT_NAME_MAP:
            return TRAIT_NAME_MAP[trait_name]
        return ""

    @staticmethod
    def get_csv_header_fields() -> list:
        """Returns the list of header fields incorporating variable names, units, and labels
        Return:
             A list of strings that can be used as the header to a CSV file
        """
        header_fields = []
        variable_names = __internal__.get_algorithm_variable_list('VARIABLE_NAMES')
        variable_units = __internal__.get_algorithm_variable_list('VARIABLE_UNITS')
        variable_units_len = len(variable_units)
        variable_labels = __internal__.get_algorithm_variable_labels()
        variable_labels_len = len(variable_labels)

        if variable_units_len != len(variable_names):
            logging.warning("The number of variable units doesn't match the number of variable names")
            logging.warning("Continuing with defined variable units")
        if variable_labels_len and variable_labels_len != len(variable_names):
            logging.warning("The number of variable labels doesn't match the number of variable names")
            logging.warning("Continuing with defined variable labels")

        logging.debug("Variable names: %s", str(variable_names))
        logging.debug("Variable labels: %s", str(variable_labels))
        logging.debug("Variable units: %s", str(variable_units))

        for idx, field_name in enumerate(variable_names):
            field_header = field_name
            if idx < variable_labels_len:
                field_header += ' %s' % variable_labels[idx]
            if idx < variable_units_len:
                field_header += ' (%s)' % variable_units[idx]
            header_fields.append(field_header)

        logging.debug("Header fields: %s", str(CSV_TRAIT_NAMES + header_fields))
        return CSV_TRAIT_NAMES + header_fields

    @staticmethod
    def get_csv_traits_table(variable_names: list) -> tuple:
        """Returns the field names and default trait values
        Arguments:
            variable_names: a list of additional trait variable names
        Returns:
            A tuple containing the list of field names and a dictionary of default field values
        """
        # Compiled traits table
        fields = __internal__.get_csv_fields(variable_names)
        traits = {}
        for field_name in fields:
            traits[field_name] = __internal__.get_default_trait(field_name)

        if hasattr(algorithm_lidar, 'CITATION_AUTHOR') and getattr(algorithm_lidar, 'CITATION_AUTHOR'):
            traits['citation_author'] = getattr(algorithm_lidar, 'CITATION_AUTHOR')
        if hasattr(algorithm_lidar, 'CITATION_TITLE') and getattr(algorithm_lidar, 'CITATION_TITLE'):
            traits['citation_title'] = getattr(algorithm_lidar, 'CITATION_TITLE')
        if hasattr(algorithm_lidar, 'CITATION_YEAR') and getattr(algorithm_lidar, 'CITATION_YEAR'):
            traits['citation_year'] = getattr(algorithm_lidar, 'CITATION_YEAR')

        return (fields, traits)

    @staticmethod
    def get_geo_traits_table():
        """Returns the field names and default trait values
        Returns:
            A tuple containing the list of field names and a dictionary of default field values
        """
        fields = __internal__.get_geo_fields()
        traits = {}
        for field_name in fields:
            traits[field_name] = ""

        return (fields, traits)

    @staticmethod
    def get_bety_traits_table(variable_names: list) -> tuple:
        """Returns the field names and default trait values
        Arguments:
            variable_names: a list of additional trait variable names
        Returns:
            A tuple containing the list of field names and a dictionary of default field values
        """
        # Compiled traits table
        fields = __internal__.get_bety_fields(variable_names)
        traits = {}
        for field_name in fields:
            traits[field_name] = __internal__.get_default_trait(field_name)

        if hasattr(algorithm_lidar, 'CITATION_AUTHOR') and getattr(algorithm_lidar, 'CITATION_AUTHOR'):
            traits['citation_author'] = getattr(algorithm_lidar, 'CITATION_AUTHOR')
        if hasattr(algorithm_lidar, 'CITATION_TITLE') and getattr(algorithm_lidar, 'CITATION_TITLE'):
            traits['citation_title'] = getattr(algorithm_lidar, 'CITATION_TITLE')
        if hasattr(algorithm_lidar, 'CITATION_YEAR') and getattr(algorithm_lidar, 'CITATION_YEAR'):
            traits['citation_year'] = getattr(algorithm_lidar, 'CITATION_YEAR')
        if hasattr(algorithm_lidar, 'ALGORITHM_METHOD') and getattr(algorithm_lidar, 'ALGORITHM_METHOD'):
            traits['method'] = getattr(algorithm_lidar, 'ALGORITHM_METHOD')

        return (fields, traits)

    @staticmethod
    def generate_traits_list(fields, traits):
        """Returns an array of trait values
        Args:
            fields(list): the list of fields to look up and return
            traits(dict): contains the set of trait values to return
        Return:
            Returns an array of trait values taken from the traits parameter
        Notes:
            If a trait isn't found, it's assigned an empty string
        """
        # compose the summary traits
        trait_list = []
        for field_name in fields:
            if field_name in traits:
                trait_list.append(traits[field_name])
            else:
                trait_list.append(__internal__.get_default_trait(field_name))

        return trait_list

    @staticmethod
    def filter_file_list_by_ext(source_files: list, known_exts: list) -> list:
        """Returns the list of known files by extension
        Arguments:
            source_files: the list of source files to look through
            known_exts: the list of known extensions
        Return:
            Returns the list of files identified as image files
        """
        return_list = []

        # Skip files we don't know about
        for one_file in source_files:
            ext = os.path.splitext(one_file)[1].strip('.')
            if ext in known_exts:
                return_list.append(one_file)

        return return_list

    @staticmethod
    def determine_csv_path(path_list: list) -> str:
        """Iterates over the list of paths and returns the first valid one
        Arguments:
            path_list: the list of paths to iterate over
        Return:
            The first found path that exists, or None if no paths are found
        """
        if not path_list:
            return None

        for one_path in path_list:
            if not one_path:
                continue
            if os.path.exists(one_path) and os.path.isdir(one_path):
                return one_path

        return None

    @staticmethod
    def get_csv_file_names(csv_path: str) -> list:
        """Returns the list of csv file paths
        Arguments:
            csv_path: the base path for the csv files
        Return:
            Returns the list of file paths: default CSV file, Geostreams CSV file, BETYdb CSV file
        """
        return [os.path.join(csv_path, FILE_NAME_CSV),
                os.path.join(csv_path, FILE_NAME_GEO_CSV),
                os.path.join(csv_path, FILE_NAME_BETYDB_CSV)]


    @staticmethod
    def validate_calc_value(calc_value, variable_names: list) -> list:
        """Returns a list of the validated value(s) as compared against type and length of variable names
        Arguments:
            calc_value: the calculated value(s) to validate (int, float, str, dict, list, etc.)
            variable_names: the list of the names of expected variables
        Return:
            Returns the validated values as a list
        Exceptions:
            RuntimeError is raised if the calc_value is not a supported type or the number of values doesn't match
            the expected number (as determined by variable_names)
        """
        if isinstance(calc_value, set):
            raise RuntimeError("A 'set' type of data was returned and isn't supported. Please use a list or a tuple instead")

        # Get the values into list form
        values = []
        len_variable_names = len(variable_names)
        if isinstance(calc_value, dict):
            # Assume the dictionary is going to have field names with their values
            # We check whether we have the correct number of fields later. This also
            # filters out extra fields
            values = []
            for key in variable_names:
                if key in calc_value:
                    values.append(calc_value[key])
        elif not isinstance(calc_value, (list, tuple)):
            values = [calc_value]

        # Sanity check our values
        len_calc_value = len(values)
        if not len_calc_value == len_variable_names:
            raise RuntimeError("Incorrect number of values returned. Expected " + str(len_variable_names) +
                               " and received " + str(len_calc_value))

        return values

    @staticmethod
    def write_trait_csv(filename: str, header: str, fields: list, traits: dict) -> None:
        """Writes the trait data to the specified CSV file
        Arguments:
            filename: the name of the file to write to
            header: the file header to be written as needed
            fields: the list of field names to save to the file
            traits: the trait values to write
        """
        trait_list = __internal__.generate_traits_list(fields, traits)
        csv_data = ','.join(map(str, trait_list))
        __internal__.write_csv_file(filename, header, csv_data)


def add_parameters(parser: argparse.ArgumentParser) -> None:
    """Adds parameters
    Arguments:
        parser: instance of argparse
    """
    supported_files = [FILE_NAME_CSV + ': basic CSV file with calculated values']
    if __internal__.get_algorithm_definition_bool('WRITE_GEOSTREAMS_CSV', True):
        supported_files.append(FILE_NAME_BETYDB_CSV + ': TERRA REF Geostreams compatible CSV file')
    if __internal__.get_algorithm_definition_bool('WRITE_BETYDB_CSV', True):
        supported_files.append(FILE_NAME_BETYDB_CSV + ': BETYdb compatible CSV file')

    parser.description = 'Plot level lidar algorithm: ' + __internal__.get_algorithm_name() + \
                         ' version ' + __internal__.get_algorithm_definition_str('VERSION', 'x.y')

    parser.add_argument('--csv_path', help='the path to use when generating the CSV files')
    parser.add_argument('--geostreams_csv', action='store_true',
                        help='override to always create the TERRA REF Geostreams-compatible CSV file')
    parser.add_argument('--betydb_csv', action='store_true', help='override to always create the BETYdb-compatible CSV file')

    parser.add_argument('germplasm_name', type=str, help='name of the cultivar associated with the plot')

    parser.epilog = 'The following files are created in the specified csv path by default: ' + \
                    '\n  ' + '\n  '.join(supported_files) + '\n' + \
                    ' author ' + __internal__.get_algorithm_definition_str('ALGORITHM_AUTHOR', 'mystery author') + \
                    ' ' + __internal__.get_algorithm_definition_str('ALGORITHM_AUTHOR_EMAIL', '(no email)')


def check_continue(transformer: transformer_class.Transformer, check_md: dict, transformer_md: list, full_md: list) -> tuple:
    """Checks if conditions are right for continuing processing
    Arguments:
        transformer: instance of transformer class
        check_md: request specific metadata
        transformer_md: metadata associated with previous runs of the transformer
        full_md: the full set of metadata available to the transformer
    Return:
        Returns a list containing the return code for continuing or not, and
        an error message if there's an error
    """
    # pylint: disable=unused-argument
    # Look for at least one image file in the list provided
    found_image = False
    for one_file in check_md['list_files']():
        ext = os.path.splitext(one_file)[1].strip('.')
        if ext in transformer.supported_image_file_exts:
            found_image = True
            break

    if not found_image:
        logging.debug("Image not found in list of files. Supported types are: %s", ", ".join(transformer.supported_image_file_exts))

    return (0) if found_image else (-1000, "Unable to find an image in the list of files")


def perform_process(transformer: transformer_class.Transformer, check_md: dict, transformer_md: dict, full_md: list) -> dict:
    """Performs the processing of the data
    Arguments:
        transformer: instance of transformer class
        check_md: metadata associated with this request
        transformer_md: metadata associated with this transformer
        full_md: the full set of metadata
    Return:
        Returns a dictionary with the results of processing
    """
    # pylint: disable=unused-argument
    # loop through the available files and clip data into plot-level files
    processed_files = 0
    processed_plots = 0
    start_timestamp = datetime.datetime.now()
    file_list = check_md['list_files']()
    files_to_process = __internal__.get_files_to_process(file_list, transformer.args.sensor, transformer.args.epsg)
    logging.info("Found %s files to process", str(len(files_to_process)))

    # Get all the possible plots
    datestamp = check_md['timestamp'][0:10]
    all_plots = get_site_boundaries(datestamp, city='Maricopa')
    logging.debug("Have %s plots for site", len(all_plots))

    container_md = []
    for filename in files_to_process:
        processed_files += 1
        file_path = files_to_process[filename]['path']
        file_bounds = files_to_process[filename]['bounds']
        sensor = files_to_process[filename]['sensor_name']
        logging.debug("File bounds: %s", str(file_bounds))

        overlap_plots = find_plots_intersect_boundingbox(file_bounds, all_plots, fullmac=True)
        logging.info("Have %s plots intersecting file '%s'", str(len(overlap_plots)), filename)

        file_spatial_ref = __internal__.get_spatial_reference_from_json(file_bounds)
        for plot_name in overlap_plots:
            processed_plots += 1
            plot_bounds = convert_json_geometry(overlap_plots[plot_name], file_spatial_ref)
            logging.debug("Clipping out plot '%s': %s", str(plot_name), str(plot_bounds))
            if __internal__.calculate_overlap_percent(plot_bounds, file_bounds) < 0.10:
                logging.info("Skipping plot with too small overlap: %s", plot_name)
                continue
            tuples = geojson_to_tuples_betydb(yaml.safe_load(plot_bounds))

            plot_md = __internal__.cleanup_request_md(check_md)
            plot_md['plot_name'] = plot_name

            if filename.endswith('.tif'):
                # If file is a geoTIFF, simply clip it
                out_path = os.path.join(check_md['working_folder'], plot_name)
                out_file = os.path.join(out_path, filename)
                if not os.path.exists(out_path):
                    os.makedirs(out_path)

                clip_raster(file_path, tuples, out_path=out_file, compress=True)

                cur_md = __internal__.prepare_container_md(plot_name, plot_md, sensor, file_path, [out_file])
                container_md = __internal__.merge_container_md(container_md, cur_md)

            elif filename.endswith('.las'):
                out_path = os.path.join(check_md['working_folder'], plot_name)
                out_file = os.path.join(out_path, filename)
                if not os.path.exists(out_path):
                    os.makedirs(out_path)

                __internal__.clip_las(file_path, tuples, out_path=out_file)

                cur_md = __internal__.prepare_container_md(plot_name, plot_md, sensor, file_path, [out_file])
                container_md = __internal__.merge_container_md(container_md, cur_md)

    return {
        'code': 0,
        'container': container_md,
        configuration.TRANSFORMER_NAME:
        {
            'utc_timestamp': datetime.datetime.utcnow().isoformat(),
            'processing_time': str(datetime.datetime.now() - start_timestamp),
            'total_file_count': len(file_list),
            'processed_file_count': processed_files,
            'total_plots_processed': processed_plots,
            'sensor': transformer.args.sensor
        }
    }