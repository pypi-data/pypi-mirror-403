import logging
import os
import gmsh
import time

from fiqus.plotters.PlotPythonMultipole import PlotPythonMultipole
from fiqus.utils.Utils import GmshUtils
from fiqus.utils.Utils import FilesAndFolders as Util
from fiqus.data import DataFiQuS as dF
from fiqus.data.DataRoxieParser import FiQuSGeometry
from fiqus.geom_generators.GeometryMultipole import Geometry
from fiqus.mesh_generators.MeshMultipole import Mesh
from fiqus.getdp_runners.RunGetdpMultipole import RunGetdpMultipole
from fiqus.getdp_runners.RunGetdpMultipole import AssignNaming
from fiqus.post_processors.PostProcessMultipole import PostProcess


class MainMultipole:
    def __init__(self, fdm: dF.FDM = None, rgd_path: str = None, verbose: bool = None, inputs_folder_path = None):
        """
        Main class for working with simulations for multipole type magnets
        :param fdm: FiQuS data model
        :param rgd_path: ROXIE geometry data path
        :param verbose: if True, more info is printed in the console
        """
        self.fdm = fdm
        self.rgd = rgd_path
        self.verbose = verbose

        self.GetDP_path = None
        self.geom_folder = None
        self.mesh_folder = None
        self.solution_folder = None
        self.inputs_folder_path = inputs_folder_path

    def force_symmetry(self):
        fdm = self.fdm.__deepcopy__()
        fdm.magnet.geometry.electromagnetics.symmetry = 'x'
        return fdm

    def generate_geometry(self, gui: bool = False):
        geom = Util.read_data_from_yaml(self.rgd, FiQuSGeometry)
        fdm = self.force_symmetry() if 'solenoid' in geom.Roxie_Data.coil.coils[1].type else self.fdm  # todo: this should be handled by pydantic
        if self.fdm.magnet.geometry.plot_preview:
            plotter = PlotPythonMultipole(geom, self.fdm)
            plotter.plot_coil_wedges()
        gg = Geometry(data=fdm, geom=geom, geom_folder=self.geom_folder, verbose=self.verbose)
        gg.saveHalfTurnCornerPositions()

        geometry_settings = {'EM': fdm.magnet.geometry.electromagnetics, 'TH': self.fdm.magnet.geometry.thermal}
        geometry_type_list = []

        if geometry_settings['EM'].create: geometry_type_list.append('EM')
        if geometry_settings['TH'].create: geometry_type_list.append('TH')
        for geometry_type in geometry_type_list:
            gg.saveStrandPositions(geometry_type)
            if any(geometry_settings[geometry_type].areas):
                gg.constructIronGeometry(geometry_settings[geometry_type].symmetry if geometry_type == 'EM' else 'none', geometry_settings[geometry_type], run_type = geometry_type)
            gg.constructCoilGeometry(geometry_type)
            if geometry_settings[geometry_type].with_wedges:
                gg.constructWedgeGeometry(geometry_settings[geometry_type].use_TSA if geometry_type == 'TH' else False)
            gmsh.model.occ.synchronize()
            if geometry_type == 'TH':
                if geometry_settings[geometry_type].use_TSA:
                    gg.constructThinShells(geometry_settings[geometry_type].with_wedges)
                else:
                    gg.constructInsulationGeometry()
                if geometry_settings[geometry_type].use_TSA_new:
                    gg.constructAdditionalThinShells()

            gg.buildDomains(geometry_type, geometry_settings[geometry_type].symmetry if geometry_type == 'EM' else 'none')
            if geometry_type == 'EM':
                gg.fragment()
            if geometry_type =='TH' and 'poles' in geometry_settings[geometry_type].areas:
                # make sure geometry is connected
                gmsh.model.occ.removeAllDuplicates()
                gmsh.model.occ.synchronize()

            gg.saveBoundaryRepresentationFile(geometry_type)
            gg.loadBoundaryRepresentationFile(geometry_type)
            gg.updateTags(geometry_type, geometry_settings[geometry_type].symmetry if geometry_type == 'EM' else 'none')
            gg.saveAuxiliaryFile(geometry_type)
            gg.clear()
        gg.ending_step(gui)

    def load_geometry(self, gui: bool = False):
        pass
        # gu = GmshUtils(self.geom_folder, self.verbose)
        # gu.initialize(verbosity_Gmsh=self.fdm.run.verbosity_Gmsh)
        # model_file = os.path.join(self.geom_folder, self.fdm.general.magnet_name)
        # gmsh.option.setString(name='Geometry.OCCTargetUnit', value='M')  # set units to meters
        # gmsh.open(model_file + '_EM.brep')
        # gmsh.open(model_file + '_TH.brep')
        # if gui: gu.launch_interactive_GUI()

    def pre_process(self, gui: bool = False):
        pass

    def load_geometry_for_mesh(self, run_type):
        gu = GmshUtils(self.geom_folder, self.verbose)
        gu.initialize(verbosity_Gmsh=self.fdm.run.verbosity_Gmsh)
        model_file = os.path.join(self.geom_folder, self.fdm.general.magnet_name)
        gmsh.option.setString(name='Geometry.OCCTargetUnit', value='M')  # set units to meters
        gmsh.open(model_file + f'_{run_type}.brep')

    def mesh(self, gui: bool = False):
        def _create_physical_group_for_reference(self):
            """
                This code generates the reference models for the FALCOND_C
            """
            ### hardcoded, we need only one reference
            if 'FALCOND_C' in self.fdm.general.magnet_name.upper() and 'POLE' in self.fdm.general.magnet_name.upper():
                CUT_REFERENCE = True # self specify loop and surf

                L_col = [56, 57, 58, 35, 16, 49, 48, 47]
                l1 = gmsh.model.occ.addLine(746,48)
                l2 = gmsh.model.occ.addLine(41,691)
                L_inner = list(range(854, 754-1, -1))
                loop1 = gmsh.model.occ.addCurveLoop([l1] + L_col + [l2] + L_inner)

                R_col = [52, 53, 54, 26, 6, 45, 44, 43]
                r1 = gmsh.model.occ.addLine(38,902)
                r2 = gmsh.model.occ.addLine(847,45)
                R_inner = list(range(910, 1010+1))
                loop2 = gmsh.model.occ.addCurveLoop([r2]+ R_col + [r1] + R_inner)

                surf1 = gmsh.model.occ.addPlaneSurface([loop1])
                surf2 = gmsh.model.occ.addPlaneSurface([loop2])
                surf = [surf1, surf2]  # tag

            else: raise Exception("Reference meshing is not implemented for this magnet.")
            gmsh.model.occ.synchronize()

            #add to physical groups / domains -> write to aux file
            file = os.path.join(self.geom_folder, self.fdm.general.magnet_name + '_TH.aux')
            with open(file) as f:
                lines = f.readlines()
            updated_lines = []
            flag = 0
            for line in lines:
                updated_lines.append(line)
                if flag == 0 and 'groups_entities:' in line:
                    flag = 1
                if flag==1 and ('ref_mesh: {}' in line):
                    if type(surf) == list:
                        updated_lines[-1] = f'    ref_mesh:\n      {self.fdm.magnet.solve.thermal.insulation_TSA.between_collar.material}: {surf}\n'
                    else:
                        updated_lines[-1] = f'    ref_mesh:\n      {self.fdm.magnet.solve.thermal.insulation_TSA.between_collar.material}: [{surf}]\n'
                        #if not CUT_REFERENCE else f'    ref_mesh:\n      {self.fdm.magnet.solve.thermal.insulation_TSA.between_collar.material}: '+ str(surf) +'\n'
                    flag = -1

            with open(file, 'w') as f:
                f.writelines(updated_lines)
            logger = logging.getLogger('FiQuS')
            logger.warning("Overwrite the .aux file to include the new domain")

        mm = Mesh(data=self.fdm, mesh_folder=self.mesh_folder, verbose=self.verbose) ## same mesh object is used for both thermal and EM
        geom = Util.read_data_from_yaml(self.rgd, FiQuSGeometry)
        fdm = self.force_symmetry() if 'solenoid' in geom.Roxie_Data.coil.coils[1].type else self.fdm
        geometry_settings = {'EM': fdm.magnet.geometry.electromagnetics, 'TH': self.fdm.magnet.geometry.thermal}
        mesh_settings = {'EM': fdm.magnet.mesh.electromagnetics, 'TH': fdm.magnet.mesh.thermal}

        mesh_type_list = []
        if mesh_settings['EM'].create: mesh_type_list.append('EM')
        if mesh_settings['TH'].create: mesh_type_list.append('TH')
        for physics_solved in mesh_type_list:
            self.load_geometry_for_mesh(physics_solved)
            if physics_solved == 'TH' and mesh_settings['TH'].reference.enabled and 'collar' in geometry_settings['TH'].areas:
                if self.fdm.magnet.geometry.thermal.use_TSA_new or self.fdm.magnet.geometry.thermal.use_TSA:
                    raise Exception('Reference solution is not implemented for collar with TSA')
                if 'iron_yoke' in geometry_settings['TH'].areas:
                    raise Exception('Reference solution is intended (read: hardcoded) without iron yoke')
                _create_physical_group_for_reference(self)
            mm.loadAuxiliaryFile(physics_solved)
            if any(geometry_settings[physics_solved].areas):
                mm.getIronCurvesTags(physics_solved)
            mm.defineMesh(geometry_settings[physics_solved], mesh_settings[physics_solved], physics_solved)
            mm.createPhysicalGroups(geometry_settings[physics_solved])
            mm.updateAuxiliaryFile(physics_solved)
            if geometry_settings[physics_solved].model_dump().get('use_TSA', False):
                mm.rearrangeThinShellsData() # rearrange data for the pro file, technically optional
            mm.assignRegionsTags(geometry_settings[physics_solved], mesh_settings[physics_solved])
            mm.saveRegionFile(physics_solved)
            mm.setMeshOptions()
            mm.generateMesh()
            mm.checkMeshQuality()
            mm.saveMeshFile(physics_solved)
            if geometry_settings[physics_solved].model_dump().get('use_TSA', False):
                mm.saveClosestNeighboursList()
                if self.fdm.magnet.mesh.thermal.isothermal_conductors: mm.selectMeshNodes(elements='conductors')
                if self.fdm.magnet.geometry.thermal.with_wedges and self.fdm.magnet.mesh.thermal.isothermal_wedges: mm.selectMeshNodes(elements='wedges')
            if geometry_settings[physics_solved].model_dump().get('use_TSA_new', False):
                mm.saveClosestNeighboursList_new_TSA()
            mm.saveHalfTurnCornerPositions()
            mm.saveRegionCoordinateFile(physics_solved)
            mm.clear()
        mm.ending_step(gui)
        return mm.mesh_parameters

    def load_mesh(self, gui: bool = False):
        gu = GmshUtils(self.geom_folder, self.verbose)
        gu.initialize(verbosity_Gmsh=self.fdm.run.verbosity_Gmsh)
        gmsh.open(f"{os.path.join(self.mesh_folder, self.fdm.general.magnet_name)}.msh")
        if gui: gu.launch_interactive_GUI()

    def solve_and_postprocess_getdp(self, gui: bool = False):
        an = AssignNaming(data=self.fdm)
        rg = RunGetdpMultipole(data=an, solution_folder=self.solution_folder, GetDP_path=self.GetDP_path, verbose=self.verbose)

        rg.loadRegionFiles()
        rg.loadRegionCoordinateFile()
        rg.read_aux_file(os.path.join(self.mesh_folder, f"{self.fdm.general.magnet_name}_EM.aux"))
        rg.extract_half_turn_blocks()
        if self.fdm.magnet.geometry.thermal.use_TSA_new:
            rg.read_aux_file(os.path.join(self.mesh_folder, f"{self.fdm.general.magnet_name}_TH.aux")) # now load the thermal aux file
            rg.extract_specific_TSA_lines()

        rg.assemblePro()
        start_time = time.time()
        rg.solve_and_postprocess()
        rg.ending_step(gui)


    def post_process_getdp(self, gui: bool = False):
        an = AssignNaming(data=self.fdm)
        rg = RunGetdpMultipole(data=an, solution_folder=self.solution_folder, GetDP_path=self.GetDP_path, verbose=self.verbose)
        rg.loadRegionFiles()
        if self.fdm.magnet.solve.thermal.solve_type and self.fdm.magnet.geometry.thermal.use_TSA:
            rg.loadRegionCoordinateFile()
        rg.assemblePro()
        rg.postprocess()
        rg.ending_step(gui)

    def post_process_python(self, gui: bool = False):
        if self.fdm.run.type == 'post_process_python_only':
            an = AssignNaming(data=self.fdm)
            data = an.data
        else: data = self.fdm

        run_types = []
        if self.fdm.magnet.solve.electromagnetics.solve_type: run_types.append('EM')
        if self.fdm.magnet.solve.thermal.solve_type: run_types.append('TH')
        pp_settings = {'EM': self.fdm.magnet.postproc.electromagnetics, 'TH': self.fdm.magnet.postproc.thermal}
        pp = PostProcess(data=data, solution_folder=self.solution_folder, verbose=self.verbose)
        for run_type in run_types:
            pp.prepare_settings(pp_settings[run_type])
            pp.loadStrandPositions(run_type)
            pp.loadAuxiliaryFile(run_type)
            if pp_settings[run_type].plot_all != 'False': pp.loadHalfTurnCornerPositions()
            if pp_settings[run_type].model_dump().get('take_average_conductor_temperature', False): pp.loadRegionFile()
            pp.postProcess(pp_settings[run_type])
            if run_type == 'EM' and self.fdm.magnet.geometry.electromagnetics.symmetry != 'none': pp.completeMap2d()
            pp.clear()
        pp.ending_step(gui)
        return pp.postprocess_parameters

    def plot_python(self):
        os.chdir(self.solution_folder)
        p = PlotPythonMultipole(self.fdm, self.fdm)
        p.plot_coil_wedges()
