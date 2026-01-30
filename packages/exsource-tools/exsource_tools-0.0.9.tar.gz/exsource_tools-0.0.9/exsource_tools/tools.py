"""
Tools for processing ExSourceFiles.
"""

import json
from copy import deepcopy
import logging
import yaml

from exsource_tools import utils
from exsource_tools.exsource import ExSource
from exsource_tools.enums import Status, Action
from exsource_tools.exporters import (OpenSCADExporter,
                                      Scad2GltfExporter,
                                      CadQueryExporter,
                                      FreeCADExporter,
                                      EngScriptExporter)

logging.basicConfig()
LOGGER = logging.getLogger('exsource')
LOGGER.setLevel(logging.INFO)



def load_exsource_file(filepath):
    """
    Load an exsource file from the inupt filepath. An ExSource object is returned
    """
    file_format = utils.exsource_file_format(filepath, "read")
    with open(filepath, 'r', encoding="utf-8") as file_obj:
        file_content = file_obj.read()
        if file_format == "JSON":
            input_data = json.loads(file_content)
        else:
            #only other option is YAML
            input_data = yaml.safe_load(file_content)
    return ExSource(input_data)

class ExSourceProcessor:
    """
    This class processes the data in the exsource file to create all the ouputs.
    Currently it only works for certain OpenSCAD, FreeCAD, CadQuery and EngScript exports
    """

    def __init__(self,
                 exsource_def,
                 previous_exsource=None,
                 exsource_out_path=None,
                 headless=False):

        self.headless = headless
        self._exsource = deepcopy(exsource_def)
        self._exsource_prev = previous_exsource
        self._exsource_out_path = exsource_out_path
        self._all_output_files = {output.filepath: Status.UNSTAGED for output in self._exsource.all_output_files}

    def check(self, echo=True):
        """
        Check which files require exporting
        """
        if self._exsource_prev is None:
            if echo:
                print("No exsource-out found.")
            return {export_id: Status.NEW for export_id in self._exsource.exports.items()}

        output = {}
        for export_id, export in self._exsource.exports.items():
            output[export_id] = self._check_dependencies(export_id, export)

            if echo:
                if output[export_id] == Status.NEW:
                    print(f"Export {export_id} not in previous run.")
                elif output[export_id] == Status.UNCHANGED:
                    print(f"Export {export_id}: is unchanged, no processing needed")
                elif output[export_id] == Status.UNCHANGED_INCOMPLETE:
                    print(f"Export {export_id}: is unchanged, however not all "
                          "dependencies are known")
                elif output[export_id] == Status.DETAILS_CHANGED:
                    print(f"Export {export_id}: outputs are unchanged, details "
                          "have been updated")
                elif output[export_id] == Status.DETAILS_CHANGED_INCOMPLETE:
                    print(f"Export {export_id}:  outputs are unchanged, details "
                          "have been updated and not all dependencies are known")
                else:
                    print(f"Export {export_id}: has changed, any ouput files need "
                          "regenerating.")
        return output

    def make(self):
        """
        Process all exsource exports (if possible)
        """
        self._all_output_files = {output.filepath: Status.PENDING for output in self._exsource.all_output_files}
        iteration = 0
        unprocessed_exports = self._exsource.exports
        while len(unprocessed_exports) > 0:
            #This is quite simplistic see issue #11
            iteration += 1
            if iteration > len(self._exsource.exports):
                raise RuntimeError("Circular dependencies in exsource file")

            unprocessed_exports = self._process_exports(unprocessed_exports)

        outpath = self._exsource_out_path
        if outpath is None:
            outpath = 'exsource-out.yml'
        self._exsource.save(outpath)

    def _process_exports(self, exports_to_process):
        unprocessed_exports = {}

        for export_id, export in exports_to_process.items():
            LOGGER.info("Processing export: %s", export_id)
            app = export.application

            dep_status = self._check_dependencies(export_id, export)
            if dep_status in [Status.UNCHANGED, Status.DETAILS_CHANGED]:
                LOGGER.info("Export %s: is unchanged, no processing needed", export_id)
                #Move all extra information over if eveything is unchanged since last run.
                # Updated details are coppied over without re running files
                new_export = deepcopy(self._exsource_prev.exports[export_id])
                new_export.name = export.name
                new_export.description = export.description
                self._exsource.exports[export_id] = new_export
                continue

            #If the dependncy was changed. Decide the action and proceed.
            action = self._decide_action(export)

            if action == Action.CONTINUE:
                if app.lower() == "openscad":
                    ose = OpenSCADExporter(export, headless=self.headless)
                    ose.process_export(output_file_statuses=self._all_output_files)
                elif app.lower() == "scad2gltf":
                    sge = Scad2GltfExporter(export, headless=self.headless)
                    sge.process_export(output_file_statuses=self._all_output_files)
                elif app.lower() == "freecad":
                    fce = FreeCADExporter(export, headless=self.headless)
                    fce.process_export(output_file_statuses=self._all_output_files)
                elif app.lower() == "cadquery":
                    cqe = CadQueryExporter(export, headless=self.headless)
                    cqe.process_export(output_file_statuses=self._all_output_files)
                elif app.lower() == "engscript":
                    ese = EngScriptExporter(export, headless=self.headless)
                    ese.process_export(output_file_statuses=self._all_output_files)
                else:
                    LOGGER.warning("Skipping %s as no methods available process files with %s",
                                   export_id,
                                   app)
                    for output in export.output_files:
                        self._all_output_files[output.filepath] = Status.SKIPPED
            elif action == Action.SKIP:
                for output in export.output_files:
                    self._all_output_files[output.filepath] = Status.SKIPPED
                LOGGER.warning("Skipping %s it has skipped dependencies", export_id)
            elif action == Action.DELAY:
                unprocessed_exports[export_id] = export
                LOGGER.info("Delaying %s as it has unprocessed dependencies", export_id)

        return unprocessed_exports

    def _check_dependencies(self, export_id, export):
        """
        Check if files need processing based on dependency and source file status
        """

        if self._exsource_prev is None:
            return Status.NEW

        if export_id not in self._exsource_prev.exports:
            return Status.NEW

        prev_export = self._exsource_prev.exports[export_id]
        if export.unchanged_from(prev_export):
            exhaustive = prev_export.dependencies_exhaustive
            if export.details_unchanged_from(prev_export):
                unchanged_status = Status.UNCHANGED if exhaustive else Status.UNCHANGED_INCOMPLETE
            else:
                unchanged_status = Status.DETAILS_CHANGED if exhaustive else Status.DETAILS_CHANGED_INCOMPLETE
            return unchanged_status
        return Status.CHANGED

    def _decide_action(self, export):
        """
        action to take based on dependency file status
        """
        action = Action.CONTINUE
        for dep in export.dependencies + export.source_files:
            dep.store_hash()
            if dep.filepath in self._all_output_files:
                dep_status = self._all_output_files[dep.filepath]
                if dep_status == Status.SKIPPED:
                    return Action.SKIP
                if dep_status == Status.PENDING:
                    LOGGER.info("Dependent file: %s not yet processed", dep.filepath)
                    action = Action.DELAY
                    #No return here as another dependency might require it to be skipped

        return action
