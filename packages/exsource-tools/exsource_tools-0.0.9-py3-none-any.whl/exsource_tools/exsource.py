"""
Classes for representing and manipulating exsource files
"""
from os import path
import json
from copy import deepcopy
import logging
import hashlib
import yaml
from jsonschema import validate

from exsource_tools import utils

logging.basicConfig()
LOGGER = logging.getLogger('exsource')
LOGGER.setLevel(logging.INFO)

SOURCE_PATH = path.dirname(__file__)
SCHEMA_PATH = path.join(SOURCE_PATH, "schemas")

class ExSource:
    """
    Class that stores and validates ExSource data.
    """

    def __init__(self, exsource_data):
        self._store(exsource_data)

    def validate(self, data):
        """
        Validate data against schema
        """
        validate(instance=data, schema=self.load_schema())

    def _store(self, data):
        """
        Store data if valid
        """
        self.validate(data)
        self._extra_data = deepcopy(data)
        self._exports = {key: ExSourceExport(data['exports'][key]) for key in data['exports']}
        del self._extra_data['exports']
        all_output_filenames = [file_obj.filepath for file_obj in self.all_output_files]
        if len(set(all_output_filenames)) != len(all_output_filenames):
            LOGGER.warning("Warning: Multiple exports define the creation of the same input file.")

    def dump(self):
        """
        Return the ExSource data as a python dictionary. This can then be dumped to file.
        """
        data = deepcopy(self._extra_data)
        data['exports'] = {key: self._exports[key].dump() for key in self._exports}
        # Check still valid, as the data may have been updated directly.
        self.validate(data)
        return data

    def save(self, filepath):
        """
        Save ExSource data to file.
        """
        file_format = utils.exsource_file_format(filepath, "write")
        with open(filepath, 'w', encoding="utf-8") as file_obj:
            if file_format == "JSON":
                json.dump(self.dump(), file_obj, sort_keys=True, indent=4)
            else:
                #only other option is YAML
                file_obj.write(yaml.dump(self.dump()))

    def set_data(self, data):
        """
        Set data from dictionary
        """
        self._store(data)

    def load_schema(self):
        """
        Return the exsource schema.
        """
        schema_file = path.join(SCHEMA_PATH, "exsource.schema.json")
        with open(schema_file, 'r', encoding="utf-8") as file_obj:
            schema = json.loads(file_obj.read())
        return schema

    @property
    def exports(self):
        """
        Return the dictionary of each key is the export name (id),
        the values are ExSourceExport objects
        """
        return self._exports

    @property
    def all_output_files(self):
        """
        A list of output files for every export combined
        """
        output_files = []
        for _, export in self.exports.items():
            output_files += export.output_files
        return output_files

    @property
    def all_input_files(self):
        """
        A list of input files for every export combined
        """
        input_files = []
        for _, export in self.exports.items():
            input_files += export.input_files
        return input_files

    def export_id_for(self, filepath):
        """
        Return the export that generates the file specified as `filepath`.
        The return is a ExSourceExport object
        """
        for export_id, export in self.exports.items():
            if filepath in export.output_files:
                return export_id
        return None


class ExSourceExport:
    """
    A class to hold the data for an exsource export
    """
    # This is mostly seriealisation and de serialisation
    # There must be a better way than this?:
    # - Keeping everything in a dictionary is rubbish.
    # - Writing a marshmallow schema for a json schema seems silly
    # - Marshmallow-jsonschema goes the wrong way

    def __init__(self, data):
        self._extra_data = deepcopy(data)
        self._output_files = [ExSourceFile(file_data) for file_data in data['output-files']]
        del self._extra_data['output-files']
        self._source_files = [ExSourceFile(file_data) for file_data in data['source-files']]
        del self._extra_data['source-files']
        self._application = data['application']
        del self._extra_data['application']

        self._name = None
        self._description = None
        self._parameters = None
        self._app_options = None
        self._dependencies = None
        self._dependencies_exhaustive = None

        self._load_optional_properties(data)

    def _load_optional_properties(self, data):
        if 'name' in data:
            self._name = data['name']
            del self._extra_data['name']
        if 'description' in data:
            self._description = data['description']
            del self._extra_data['description']
        if 'parameters' in data:
            self._parameters = data['parameters']
            del self._extra_data['parameters']
        if 'app-options' in data:
            self._app_options = data['app-options']
            del self._extra_data['app-options']
        if 'dependencies' in data:
            self._dependencies = [ExSourceFile(file_data) for file_data in data['dependencies']]
            del self._extra_data['dependencies']
        if 'dependencies-exhaustive' in data:
            self._dependencies_exhaustive = data['dependencies-exhaustive']
            del self._extra_data['dependencies-exhaustive']

    def unchanged_from(self, previous):
        """
        Return true if this export is unchanged from a previous run. This will check the file
        hashes on disk.
        Details like the name and description are ignored. See details_unchanged_from()
        """

        if not isinstance(previous, ExSourceExport):
            return False
        if self.application != previous.application:
            return False
        if self.parameters != previous.parameters:
            return False
        if set(self.app_options) != set(previous.app_options):
            return False
        source_unchanged = self._source_files_unchanged(previous)
        output_unchanged = self._output_files_unchanged(previous)
        deps_unchanged = self._dependencies_unchanged(previous)

        return source_unchanged and output_unchanged and deps_unchanged

    def details_unchanged_from(self, previous):
        """
        Return true if details like the name and description have changed.
        To check the dependencies and file statuses, see unchanged_from()
        """
        if not isinstance(previous, ExSourceExport):
            return False
        if self.name != previous.name:
            return False
        if self.description != previous.description:
            return False
        return True

    def _source_files_unchanged(self, previous):
        if len(self.source_files) != len(previous.source_files):
            return False
        for source_file, previous_source_file in zip(self.source_files, previous.source_files):
            if source_file.filepath != previous_source_file:
                return False
            if not previous_source_file.unchanged_on_disk:
                return False
        return True

    def _output_files_unchanged(self, previous):
        if len(self.output_files) != len(previous.output_files):
            return False
        for output_file, previous_output_file in zip(self.output_files, previous.output_files):
            if output_file.filepath != previous_output_file:
                return False
            if not previous_output_file.unchanged_on_disk:
                return False
        return True

    def _dependencies_unchanged(self, previous):
        for dep in previous.dependencies:
            if not dep.unchanged_on_disk:
                return False
        return True


    def __getitem__(self, key):
        return dict.__getitem__(self._extra_data, key)

    def dump(self):
        """
        Return the data for this export as a python dictionary.
        """
        data = deepcopy(self._extra_data)
        data['output-files'] = [file_obj.dump() for file_obj in self._output_files]
        data['source-files'] = [file_obj.dump() for file_obj in self._source_files]
        data['application'] = self._application
        if self._name is not None:
            data['name'] = self._name
        if self._description is not None:
            data['description'] = self._description
        if self._parameters is not None:
            data['parameters'] = self._parameters
        if self._app_options is not None:
            data['app-options'] = self._app_options
        if self._dependencies is not None:
            data['dependencies'] = [file_obj.dump() for file_obj in self._dependencies]
        if self._dependencies_exhaustive is not None:
            data['dependencies-exhaustive'] = self._dependencies_exhaustive
        return data

    @property
    def output_files(self):
        """
        Return the list of output files
        """
        return self._output_files

    @property
    def source_files(self):
        """
        Return the list of source files
        """
        return self._source_files

    @property
    def application(self):
        """
        Return the application used to perform the export
        """
        return self._application

    @property
    def name(self):
        """
        Return the name of the export
        """
        return self._name

    @name.setter
    def name(self, value):
        """
        Set the export name. This is the human freindly name.
        """
        if value is not None:
            if not isinstance(value, str):
                raise TypeError("Name must be a string")
        self._name = value

    @property
    def description(self):
        """
        Return the description of the export
        """
        return self._description

    @description.setter
    def description(self, value):
        """
        Set the export description. This is the human freindly description.
        """
        if value is not None:
            if not isinstance(value, str):
                raise TypeError("Description must be a string")
        self._description = value

    @property
    def parameters(self):
        """
        Return the parameters to be used for export
        """
        if self._parameters is None:
            return {}
        return self._parameters

    @property
    def app_options(self):
        """
        Return the application commandline options to be used for export
        """
        if self._app_options is None:
            return []
        return self._app_options

    @property
    def dependencies(self):
        """
        Return the list of dependencies
        """
        if self._dependencies is None:
            return []
        return self._dependencies

    @property
    def dependencies_exhaustive(self):
        """
        Return whether the dependencies list is exhaustive
        """
        if self._dependencies_exhaustive is None:
            return False
        return self._dependencies_exhaustive

    def add_dependency(self, filepath, store_hash=False):
        """
        Add a dependency to this export
        """
        if self._dependencies is None:
            self._dependencies = []
        self._dependencies.append(ExSourceFile(filepath))
        if store_hash:
            self._dependencies[-1].store_hash()

    def mark_dependencies_exhaustive(self):
        """
        Mark that the dependency list is now exhaustive
        """
        self._dependencies_exhaustive = True


class ExSourceFile:
    """
    Class to store the information for a file. This could just be the filepath
    but can also contain the MD5 hash.
    """

    def __init__(self, data):
        if isinstance(data, str):
            self._filepath = data
            self._md5 = None
            self._extra_data = {}
        elif isinstance(data, dict):
            self._extra_data = deepcopy(data)
            self._filepath = data['filepath']
            del self._extra_data['filepath']
            self._md5 = data['md5']
            del self._extra_data['md5']
        else:
            raise TypeError("Expecting a dictionary or a string")

    def __eq__(self, other):
        if isinstance(other, str):
            return self.filepath == other
        if isinstance(other, ExSourceFile):
            if self.md5 is None or self.md5 == other.md5:
                if self.filepath == other.filepath:
                    return True
            return False
        return super().__eq__(other)

    def __repr__(self):
        return self._filepath

    def dump(self):
        """
        Return the data for this file as a python dictionary.
        """
        if self._extra_data == {} and self._md5 is None:
            return self._filepath

        data = deepcopy(self._extra_data)
        data['filepath'] = self._filepath
        data['md5'] = self._md5
        return data

    def store_hash(self):
        """
        Store the hash for this file if it exists
        """
        if self.exists:
            self._md5 = self.get_hash_on_disk()

    def get_hash_on_disk(self):
        """
        Return the hash for this file if it exists
        """
        if not self.exists:
            return None
        hash_md5 = hashlib.md5()
        with open(self._filepath, "rb") as file_obj:
            for chunk in iter(lambda: file_obj.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @property
    def exists(self):
        """
        Return whether this file exists on disk
        """
        return path.isfile(self._filepath)

    @property
    def filepath(self):
        """
        Return the filepath of this file
        """
        return self._filepath

    @property
    def md5(self):
        """
        Return the md5 sum of this file. This will be none if the file
        hasn't been hashed. To hash the file use store_hash.
        """
        return self._md5

    @property
    def unchanged_on_disk(self):
        """
        Return false if the file has changed on disk
        """
        if self._md5 is None:
            #Can't know if changed, so assumed to have changed
            return False
        if not self.exists:
            return False
        return self.get_hash_on_disk() == self._md5
