"""
Classes for exporting hardware files
"""
from os import path
import subprocess
import logging
from tempfile import gettempdir

from exsource_tools import utils
from exsource_tools.enums import Status

logging.basicConfig()
LOGGER = logging.getLogger('exsource')
LOGGER.setLevel(logging.INFO)

class BaseExporter:
    """
    This is a base class for exporters. Don't try to run this class
    The exporter runs one "export" from the exsorce. It will export
    all output files. Input to init is one ExSourceExport object.
    """

    name = "Base"
    executable = None
    min_outputs = 1
    max_outputs = None
    min_sources = 1
    max_sources = None
    # True if all outputs are a single call
    single_call = False

    def __init__(self, export, headless=False):
        self.export = export
        self.headless = headless

    @property
    def output_files(self):
        """
        Property shorthand returning all output files as a list of
        ExSourceFile objects
        """
        return self.export.output_files

    @property
    def source_files(self):
        """
        Property shorthand returning all source files as a list of
        ExSourceFile objects
        """
        return self.export.source_files

    @property
    def outputs_valid(self):
        """
        Check if there are the expected number of outputs. Return True if valid
        """
        if len(self.output_files) < self.min_outputs:
            LOGGER.warning("%s expects a minimum of %d outputs to be specified",
                           self.name, self.min_outputs)
            return False
        if self.max_outputs is not None:
            if len(self.output_files) > self.max_outputs:
                LOGGER.warning("%s expects a maximum of %d outputs to be specified",
                               self.name, self.min_outputs)
                return False
        return True

    @property
    def sources_valid(self):
        """
        Check if there are the expected number of sources. Check sources exist
        on disk. Return True if valid
        """
        if len(self.source_files) < self.min_sources:
            LOGGER.warning("%s expects a minimum of %d sources to be specified",
                           self.name, self.min_sources)
            return False
        if self.max_sources is not None:
            if len(self.source_files) > self.max_sources:
                LOGGER.warning("%s expects a maximum of %d sources to be specified",
                               self.name, self.min_sources)
                return False
        for source in self.source_files:
            if not path.exists(source.filepath):
                LOGGER.warning("Source file %s does not exist, skipping.",
                               source.filepath)
                return False
        return True

    def x_required(self, output): #pylint: disable=unused-argument
        """
        Return true if an X server is required to create this output. This will
        use xvfb-run to run the command if exsource has been run in headless mode.
        """
        return False

    @property
    def parameter_agruments(self):
        """
        Not implemented in this class. Child classes should reimplement this
        to return a list of arguments to be passed into the subprocess call
        """
        raise NotImplementedError

    def file_arguments(self, output):
        """
        Not implemented in this class. Child classes should reimplement this
        to return a list of file arguments to be passed into the subprocess call
        """
        raise NotImplementedError

    @property
    def option_arguments(self):
        """
        Splits up the application options into a list for the subprocess call
        """
        return utils.split_app_options(self.export.app_options)

    def handle_dependencies(self, output): #pylint: disable=unused-argument
        """
        If the exporter can automatically track dependencies to be added to the
        exsource-out file then this tracking should be implemented in this class
        """

    def print_output_on_success(self, ret):
        """
        Print to console the output from a successful output generation
        """
        std_out = ret.stdout.decode('UTF-8')
        print(std_out)

    def output_str_from_error(self, err):
        """
        Return the text output from a successful output generation
        """
        std_out = err.stdout.decode('UTF-8')
        std_err = err.stderr.decode('UTF-8')
        return f"{std_out}\n{std_err}"

    def check_return_for_hidden_error(self, ret, output):  #pylint: disable=unused-argument
        """
        Not implemented in the base class. This can be used to check what is returned
        from a program call to check for errors as not every program sets a non-zero
        error code on failure.
        """

    def run_executable(self, output, require_x, file_args_first=False):
        """
        Run the executable to generate the output.
        """
        params = self.parameter_agruments
        file_args = self.file_arguments(output)
        options = self.option_arguments

        if file_args_first:
            all_args = file_args + options + params
        else:
            all_args = options + params + file_args

        try:
            if self.headless and require_x:
                xrvb_args = ['xvfb-run',
                            '--auto-servernum',
                            '--server-args',
                            '-screen 0 1024x768x24']
                args = xrvb_args + [self.executable] + all_args
            else:
                args = [self.executable] + all_args
            ret = subprocess.run(args, check=True, capture_output=True)
            self.print_output_on_success(ret)
            self.check_return_for_hidden_error(ret, output)
        except subprocess.CalledProcessError as err:
            out_str = self.output_str_from_error(err)
            raise RuntimeError(f"\n\n{self.name} failed create file: {output}"
                               f" with error:\n\n{out_str}") from err

    def process_export(self, output_file_statuses):
        """
        This is the what should be called after initalisation to generate the ouput file
        """
        valid = self.outputs_valid and self.sources_valid

        if not valid:
            for output in self.output_files:
                output_file_statuses[output.filepath] = Status.SKIPPED
            return

        if self.single_call:
            require_x = False
            for output in self.output_files:
                utils.add_directory_if_needed(output.filepath)
                require_x = require_x or self.x_required(output)
            self.run_executable(self.output_files, require_x)
            for output in self.output_files:
                output.store_hash()
                self.handle_dependencies(output)
                output_file_statuses[output.filepath] = Status.PROCESSED
        else:
            for output in self.output_files:
                utils.add_directory_if_needed(output.filepath)
                require_x = self.x_required(output)
                self.run_executable(output, require_x)
                output.store_hash()
                self.handle_dependencies(output)
                output_file_statuses[output.filepath] = Status.PROCESSED


class OpenSCADExporter(BaseExporter):
    """
    This is a exporter class for OpenSCAD.
    """

    name = "OpenSCAD"
    executable = "openscad"
    min_outputs = 1
    max_outputs = 1
    min_sources = 1
    max_sources = 1

    def x_required(self, output):
        """
        Set that an x-server is required if this output is a PNG
        """
        return output.filepath.lower().endswith('.png')

    @property
    def parameter_agruments(self):
        """
        Parse the parameters into a list of the command line arguments to be used
        for the subprocess call
        """
        params = []
        for parameter in self.export.parameters:
            try:
                par = _scad_par_to_str(self.export.parameters[parameter])
            except ValueError:
                LOGGER.warning("Can only process string, numerical or boolean arguments "
                               "for OpenSCAD. Skipping parameter %s", parameter)
                continue
            params.append("-D")
            params.append(f"{parameter}={par}")
        return params

    def depfilename(self, output):
        """
        Return the depfilename for the specified output
        """
        return output.filepath + ".d"

    def file_arguments(self, output):
        """
        Return the list of the command line arguments that specify source,
        output, and dependency files to be used for the subprocess call
        """
        return ["-d", self.depfilename(output),
                "-o", output.filepath,
                self.source_files[0].filepath]

    def handle_dependencies(self, output):
        depsfile = utils.Depsfile(self.depfilename(output))
        assert len(depsfile.rules) == 1, "Expecting only one rule in and openscad deps file"
        assert len(depsfile.rules[0].outputs) == 1, "Expecting only one output to be specified in the openscad depsfile"
        assert path.normpath(depsfile.rules[0].outputs[0]) == path.normpath(output.filepath), "depsfile output doens't match expected file"
        for dep in depsfile.rules[0].dependencies:
            if dep not in self.source_files+self.export.dependencies:
                self.export.add_dependency(dep, store_hash=True)
        self.export.mark_dependencies_exhaustive()

    def print_output_on_success(self, ret):
        """Overloaded as OpenSCAD writes everything to stderr"""
        std_err = ret.stderr.decode('UTF-8')
        print(std_err)

def _scad_par_to_str(parameter):
    if isinstance(parameter, bool):
        #ensure lowercase for booleans
        return str(parameter).lower()
    if isinstance(parameter, (float, int)):
        return str(parameter)
    if isinstance(parameter, str):
        return '"'+parameter+'"'
    if isinstance(parameter, list):
        if len(parameter) == 0:
            return "[]"
        return '[' + ','.join([_scad_par_to_str(sub_par) for sub_par in parameter]) + ']'
    raise(ValueError("Wrong type"))

class Scad2GltfExporter(BaseExporter):
    """
    This is a exporter class for scad2gltf.
    """

    name = "scad2gltf"
    executable = "scad2gltf"
    min_outputs = 1
    max_outputs = 1
    min_sources = 1
    max_sources = 1

    @property
    def parameter_agruments(self):
        """
        Parse the parameters into a list of the command line arguments to be used
        for the subprocess call
        """
        params = []
        for parameter in self.export.parameters:
            try:
                par = _scad_par_to_str(self.export.parameters[parameter])
            except ValueError:
                LOGGER.warning("Can only process string, numerical or boolean arguments "
                               "for OpenSCAD. Skipping parameter %s", parameter)
                continue
            params.append("-D")
            params.append(f"{parameter}={par}")
        return params

    def file_arguments(self, output):
        """
        Return the list of the command line arguments that specify source,
        output, and dependency files to be used for the subprocess call
        """
        return [self.source_files[0].filepath, "-o", output.filepath]

    def run_executable(self, output, require_x, file_args_first=False):
        """
        Overload to force file args first
        """
        super().run_executable(output, require_x, file_args_first=True)

class CadQueryExporter(BaseExporter):
    """
    This is a exporter class for CadQuery.
    """

    name = "CadQuery"
    executable = "cq-cli"
    min_outputs = 1
    max_outputs = None
    min_sources = 1
    max_sources = 1

    @property
    def parameter_agruments(self):
        """
        Parse the parameters into a list of the command line arguments to be used
        for the subprocess call
        """
        if len(self.export.parameters) == 0:
            return []

        # Process the parameters into a string that cq-cli will understand
        params = ""
        for param in self.export.parameters:
            params += f"{param}:{self.export.parameters[param]};"
        return ["--params", params]

    def file_arguments(self, output):
        """
        Return the list of the command line arguments that specify source and
        output files to be used for the subprocess call
        """
        source = self.source_files[0]
        return [ "--infile", source.filepath, "--outfile", output.filepath]

class FreeCADExporter(BaseExporter):
    """
    This is a exporter class for FreeCAD.
    """

    name = "FreeCAD"
    executable = "freecadcmd"
    min_outputs = 1
    max_outputs = None
    min_sources = 1
    max_sources = 1

    def __init__(self, export, headless=False):
        super().__init__(export, headless)
        self.selection = "Body"
        if "object-selected" in self.export.parameters:
            self.selection = self.export.parameters["object-selected"]

    @property
    def parameter_agruments(self):
        """
        Parse the parameters into a list of the command line arguments to be used
        for the subprocess call
        """
        for parameter in self.export.parameters:
            if parameter == "object-selected":
                continue
            LOGGER.info("Cannot process parameter %s for FreeCAD, skipping",
                        parameter)
        return []

    def file_arguments(self, output):
        """
        Return the list of the command line arguments that specify source and
        output files to be used for the subprocess call. In this FreeCAD case
        as we are using a macro we only spefify the macro that was created in
        _create_macro. This macro sets the source and export files
        """
        macropath = self._create_macro(output)
        return [macropath]

    def _create_macro(self, output):
        """Freecad doesn't provide a cli for exporting so a macro must be created"""

        sourcefile = self.source_files[0].filepath
        outfile  = output.filepath
        selection_macro = (f"doc = FreeCAD.openDocument('{sourcefile}')\n"
                           f"object = doc.getObjectsByLabel('{self.selection}')[0]\n")

        if outfile.lower().endswith('.stp') or outfile.lower().endswith('.step'):
            macro = (selection_macro +
                     f"object.Shape.exportStep('{outfile}')\n")
        elif outfile.lower().endswith('.stl'):
            macro = ("from FreeCAD import Mesh\n" +
                     selection_macro +
                     f"Mesh.export([object], '{outfile}')\n")
        else:
            raise ExSourceFileTypeError(f"No method set for exporting {outfile} with FreeCAD")

        tmpdir = gettempdir()
        macropath = path.join(tmpdir, "export.FCMacro")
        with open(macropath, 'w', encoding="utf-8") as file_obj:
            file_obj.write(macro)
        return macropath

    def check_return_for_hidden_error(self, ret, output):
        """freecadcmd outputs zero error code even if script failed."""
        std_err = ret.stderr.decode('UTF-8')
        if (len(std_err)) > 0:
            raise RuntimeError(f"\n\n{self.name} failed create file: {output.filepath}"
                               f" with error:\n\n{std_err}")


class EngScriptExporter(BaseExporter):
    """
    This is a exporter class for EngScript.
    """

    name = "EngScript"
    executable = "engscript"
    min_outputs = 1
    max_outputs = None
    min_sources = 1
    max_sources = 1
    single_call = True

    def x_required(self, output):
        """
        Set that an x-server is required if this output is a PNG
        """
        return output.filepath.lower().endswith('.png')

    @property
    def parameter_agruments(self):
        """
        Parse the parameters into a list of the command line arguments to be used
        for the subprocess call
        """
        if len(self.export.parameters) == 0:
            return []

        # Process the parameters into a string that cq-cli will understand
        params = []
        for param in self.export.parameters:
            params += ["--arg", f"{param}: {self.export.parameters[param]}"]
        return params

    def file_arguments(self, output):
        """
        Return the list of the command line arguments that specify source and
        output files to be used for the subprocess call
        """
        source_file = self.source_files[0].filepath
        name, _ext = path.splitext(path.normpath(source_file))
        
        source_module = name.replace(path.sep, ".")
        output_args = []
        for item in output:
            output_args += ["-o", item.filepath]
        return output_args + [source_module]

class ExSourceFileTypeError(Exception):
    pass

