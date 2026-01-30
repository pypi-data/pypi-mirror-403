import os
import pathlib
import subprocess
import logging
import timeit
import re
import pandas as pd

import gmsh
from fiqus.pro_assemblers.ProAssembler import ASS_PRO as aP
from fiqus.utils.Utils import GmshUtils
from fiqus.utils.Utils import FilesAndFolders as Util
from fiqus.data import DataFiQuS as dF
from fiqus.data import RegionsModelFiQuS as rM
from fiqus.data import DataMultipole as dM

logger = logging.getLogger('FiQuS')

trigger_time_deactivated = 99999

class AssignNaming:
    def __init__(self, data: dF.FDM() = None):
        """
        Class to assign naming convention
        :param data: FiQuS data model
        """
        self.data: dF.FDM() = data

        self.naming_conv = {'omega': 'Omega',
                            'boundary': 'Bnd_',
                            'powered': '_p', 'induced': '_i',
                            'air': '_a',
                            'air_far_field': '_aff',
                            'conducting': '_c',
                            'insulator': '_ins',
                            'terms': 'Terms',
                            'iron_yoke': '_bh', #todo: consider renaming this
                            'collar': '_collar',
                            'ref_mesh': '_refmesh',
                            'poles': '_poles'}

        self.data.magnet.postproc.electromagnetics.volumes = \
            [self.naming_conv['omega'] + (self.naming_conv[var] if var != 'omega' else '') for var in
             self.data.magnet.postproc.electromagnetics.volumes]
        self.data.magnet.postproc.thermal.volumes = \
            [self.naming_conv['omega'] + (self.naming_conv[var] if var != 'omega' else '') for var in
             self.data.magnet.postproc.thermal.volumes]


class RunGetdpMultipole:
    def __init__(self, data: AssignNaming = None, solution_folder: str = None, GetDP_path: str = None,
                 verbose: bool = False):
        """
        Class to solve pro file
        :param data: FiQuS data model
        :param GetDP_path: settings data model
        :param verbose: If True more information is printed in python console.
        """
        logger.info(
            f"Initializing Multipole runner for {os.path.basename(solution_folder)}."
        )
        self.data: dF.FDM() = data.data
        self.naming_conv: dict = data.naming_conv
        self.solution_folder = solution_folder
        self.GetDP_path = GetDP_path
        self.verbose: bool = verbose
        self.call_method = 'subprocess'  # or onelab or subprocess or alt_solver

        self.rm_EM = rM.RegionsModel()
        self.rm_TH = rM.RegionsModel()
        self.aux = {
            "half_turns": {
                "ht": {},  # Dictionary to store half-turn data
                "max_reg": None,  # Maximum region number to avoid overlaps of physical regions
                "block": {}  # Dictionary that stores the relation between magnet blocks(groups) and half-turn areas

            },
            "e_cliq": {},  # Dictionary that stores the E-CLIQ source current LUTs from a csv
            "tsa_collar": {},
            "sim_info": {
                'date': '',
                'author': ''
            }
        }
        self.material_properties_model = None
        self.rohm = {}  # rohm parameter dictionary
        self.rohf = {}  # rohf parameter dictionary
        self.rc = dM.MultipoleRegionCoordinate() \
            if self.data.magnet.mesh.thermal.isothermal_conductors and self.data.magnet.solve.thermal.solve_type else None

        self.gu = GmshUtils(self.solution_folder, self.verbose)
        self.gu.initialize(verbosity_Gmsh=self.data.run.verbosity_Gmsh)
        self.occ = gmsh.model.occ
        self.mesh = gmsh.model.mesh
        self.brep_curves = {}
        for name in self.data.magnet.geometry.electromagnetics.areas:
            self.brep_curves[name] = {1: set(), 2: set(), 3: set(), 4: set()}
        self.mesh_files = os.path.join(os.path.dirname(self.solution_folder), self.data.general.magnet_name)
        self.model_file = os.path.join(self.solution_folder, 'Center_line.csv')

        self.mf = {'EM': f"{self.mesh_files}_EM.msh", 'TH': f"{self.mesh_files}_TH.msh"}

    def loadRegionFiles(self):
        """
        Read the regions' files and store the information in a variable. used for extracting the maximum region number.
        :param
        :return: Data from the regions files
        """
        if self.data.magnet.solve.electromagnetics.solve_type:
            self.rm_EM = Util.read_data_from_yaml(f"{self.mesh_files}_EM.reg", rM.RegionsModel)
        if self.data.magnet.solve.thermal.solve_type:
            self.rm_TH = Util.read_data_from_yaml(f"{self.mesh_files}_TH.reg", rM.RegionsModel)

    def loadRegionCoordinateFile(self):
        """
        Read the reco file and store the information in a variable.
        :param
        :return: Data from the reco file
        """
        self.rc = Util.read_data_from_yaml(f"{self.mesh_files}_TH.reco", dM.MultipoleRegionCoordinate)

    def assemblePro(self):
        """
        Assemble the .pro file using the right template depending on the inputs from the yaml
        :param
        :return: Assembled .pro file
        """
        logger.info(f"Assembling pro file...")
        start_time = timeit.default_timer()
        ap = aP(file_base_path=os.path.join(self.solution_folder, self.data.general.magnet_name),
                naming_conv=self.naming_conv)
        BH_curves_path = os.path.join(pathlib.Path(os.path.dirname(__file__)).parent, 'pro_material_functions',
                                      'ironBHcurves.pro')
        template = 'Multipole_template.pro'
        ap.assemble_combined_pro(template=template, rm_EM=self.rm_EM, rm_TH=self.rm_TH, rc=self.rc, dm=self.data,
                                 mf=self.mf, BH_curves_path=BH_curves_path, aux=self.aux)
        logger.info(
            f"Assembling pro file took"
            f" {timeit.default_timer() - start_time:.2f} s."
        )

    def solve_and_postprocess(self):
        """
        Generates the necessary GetDP commands to solve and postprocess the model, and runs them.
        :param
        :return: None
        """
        commands = None
        if self.call_method == 'onelab':
            commands = f"-solve -v2 -pos -verbose {self.data.run.verbosity_GetDP}"
        elif self.call_method == 'subprocess':
            commands = [["-solve", 'resolution', "-v2", "-pos", "Dummy", "-verbose", str(self.data.run.verbosity_GetDP),
                         "-mat_mumps_icntl_14", "250"]]
        self._run(commands=commands)

    def postprocess(self):
        """
        Generates the necessary GetDP commands to postprocess the model, and runs them.
        :param
        :return: None
        """
        if self.call_method == 'onelab':
            commands = f"-v2 -pos -verbose {self.data.run.verbosity_GetDP}"
        elif self.call_method == 'subprocess':
            commands = [["-v2", "-pos", "Dummy", "-verbose", str(self.data.run.verbosity_GetDP)]]
        elif self.call_method == 'alt_solver':
            commands = [["-solve", 'resolution', "-v2", "-pos", "Dummy"]]

        self._run(commands=commands)

    def _run(self, commands):
        """
        runs GetDP with the specified commands. Additionally it captures and logs the output.
        :param commands: List of commands to run GetDP with
        :return: None
        """
        logger.info("Solving...")
        start_time = timeit.default_timer()
        if self.call_method == 'onelab':
            for command in commands:
                gmsh.onelab.run(f"{self.data.general.magnet_name}",
                                f"{self.GetDP_path} {os.path.join(self.solution_folder, self.data.general.magnet_name)}.pro {command}")
            gmsh.onelab.setChanged("GetDP", 0)
        elif self.call_method == 'subprocess' or self.call_method == 'alt_solver':
            # subprocess.call([f"{self.GetDP_path}", f"{os.path.join(self.solution_folder, self.data.general.magnet_name)}.pro"] + command + ["-msh", f"{self.mesh_files}.msh"])

            # view_tag = gmsh.view.getTags()  # this should be b
            # # # v = "View[" + str(gmsh.view.getIndex('b')) + "]"
            # gmsh.view.write(view_tag, f"{os.path.join(self.solution_folder, self.data.general.magnet_name)}-view.msh")

            if self.data.magnet.solve.noOfMPITasks:
                mpi_prefix = ["mpiexec", "-np", str(self.data.magnet.solve.noOfMPITasks)]
            else:
                mpi_prefix = []

            for command in commands:
                use_predefined_pro = False  # If True, one can use a predefined .pro file
                if use_predefined_pro:
                    logger.warning("Using predefined .pro file")
                    getdpProcess = subprocess.Popen(
                        mpi_prefix + [f"{self.GetDP_path}",
                                      f"{os.path.join(os.path.abspath(os.path.join(self.solution_folder, '..', '..', '..')), '_out/TEST')}.pro"] +
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                    )
                else:
                    getdpProcess = subprocess.Popen(
                        mpi_prefix + [f"{self.GetDP_path}",
                                      f"{os.path.join(self.solution_folder, self.data.general.magnet_name)}.pro"] +
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                    )
                with getdpProcess.stdout:
                    for line in iter(getdpProcess.stdout.readline, b""):
                        line = line.decode("utf-8").rstrip()
                        line = line.split("\r")[-1]
                        if "Info" in line:
                            parsedLine = re.sub(r"Info\s*:\s*", "", line)
                            logger.info(parsedLine)
                        elif "Warning" in line:
                            parsedLine = re.sub(r"Warning\s*:\s*", "", line)
                            logger.warning(parsedLine)
                        elif "Error" in line:
                            parsedLine = re.sub(r"Error\s*:\s*", "", line)
                            logger.error(parsedLine)
                            raise Exception(parsedLine)
                        elif "Critical" in line:
                            parsedLine = re.sub(r"Critical\s*:\s*", "", line)
                            logger.critical(parsedLine)
                        # catch the maximum temperature line
                        elif "Maximum temperature" in line:
                            parsedLine = re.sub(r"Print\s*:\s*", "", line)
                            logger.info(parsedLine)
                        # this activates the debugging message mode
                        elif self.data.run.verbosity_GetDP > 99:
                            logger.info(line)

                getdpProcess.wait()

        logger.info(
            f"Solving took {timeit.default_timer() - start_time:.2f} s."
        )

    def ending_step(self, gui: bool = False):
        """
        Finalize the GetDP runner, either by launching the GUI or finalizing gmsh.
        :param gui: If True, launches the interactive GUI; otherwise finalizes gmsh.
        :return: None
        """
        if gui:
            self.gu.launch_interactive_GUI()
        else:
            if gmsh.isInitialized():
                gmsh.clear()
                gmsh.finalize()

    def read_aux_file(self, aux_file_path):
        """
        Read the auxiliary file and store the information in a variable. Necessary to extract half-turn information from blocks.
        :param aux_file_path: Path to the auxiliary file
        :return: Data from the auxiliary file
        """
        try:
            self.aux_data = Util.read_data_from_yaml(aux_file_path, dM.MultipoleData)
            logger.info(f"Auxiliary data loaded from {aux_file_path}")
        except FileNotFoundError:
            logger.error(f"Auxiliary file not found: {aux_file_path}")
        except Exception as e:
            logger.error(f"Error reading auxiliary file: {e}")

    def extract_half_turn_blocks(self):
        """
        Extract a dictionary from the .aux file where the keys are integers corresponding to the block number
        and the dictionary entries for these keys are a list of all the half-turn areas included in that block.
        :return: Dictionary with block numbers as keys and lists of half-turn areas as values
        """
        aux_data = self.aux_data

        half_turn_areas = {}
        info_block = {}
        coils = aux_data.geometries.coil.coils
        for coil_nr, coil_data in coils.items():
            poles = coil_data.poles
            for pole_nr, pole_data in poles.items():
                layers = pole_data.layers
                for layer_nr, layer_data in layers.items():
                    windings = layer_data.windings
                    for winding_nr, winding_data in windings.items():
                        blocks = winding_data.blocks
                        for block_nr, block_data in blocks.items():
                            half_turns = block_data.half_turns.areas
                            info_block[block_nr] = [int(area) for area in half_turns.keys()]
                            half_turn_areas[int(block_nr)] = [int(area) for area in half_turns.keys()]

        self.aux["half_turns"]["ht"] = half_turn_areas
        self.aux["half_turns"]["block"] = info_block
        pass

    def extract_specific_TSA_lines(self):
        """
        Extract a dictionary from the thermal .aux file, collects the outer lines of the half-turns and wedges used for the TSA collar
        """
        aux_data = self.aux_data
        pg = aux_data.domains.physical_groups
        max_layer = len([k for k in self.aux_data.geometries.coil.coils[1].poles[1].layers.keys()])  # todo : more elegant way ? @emma
        tags = []
        for block in pg.blocks.values():
            for ht in block.half_turns.values():
                if ht.group[-1] == str(max_layer):  # r1_a2 or r2_a2
                    tags.append(ht.lines['o'])
        self.aux["tsa_collar"]['ht_lines'] = tags

        tags = []
        for wedge in pg.wedges.values():
            if wedge.group[-1] == str(max_layer):  # r1_a2 or r2_a2
                tags.append(wedge.lines['o'])
        self.aux["tsa_collar"]['wedge_lines'] = tags
        pass