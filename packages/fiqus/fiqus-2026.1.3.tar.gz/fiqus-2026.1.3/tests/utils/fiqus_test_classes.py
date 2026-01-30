import unittest
import os
import filecmp
import gmsh
import logging
import shutil
from typing import Union, Tuple, Literal, List
import ruamel.yaml
import numpy as np
import csv

from fiqus.data.DataFiQuS import FDM
from fiqus.MainFiQuS import MainFiQuS
from fiqus.utils.Utils import GmshUtils
from fiqus.parsers.ParserCOND import ParserCOND
from fiqus.parsers.ParserMSH import ParserMSH
from fiqus.utils.Utils import FilesAndFolders as FFs

logger = logging.getLogger(__name__)


class BaseClassesForTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Change the working directory to the directory where this file's parent
        # directory is located (tests folder):
        os.chdir(os.path.dirname(os.path.dirname(__file__)))
        cls.inputs_folder = os.path.join(os.getcwd(), "_inputs")
        cls.outputs_folder = os.path.join(os.getcwd(), "_outputs")
        cls.references_folder = os.path.join(os.getcwd(), "_references")

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def setUp(self) -> None:
        """
        This method is executed before each test in this class.

        It changes the working directory to the directory where this file is located.
        """
        # Change the working directory to the directory where this file's parent
        # directory is located (tests folder):
        os.chdir(os.path.dirname(os.path.dirname(__file__)))

    def tearDown(self) -> None:
        pass

    def get_input_file_path(self, model_name: str) -> Union[str, os.PathLike]:
        """
        This method returns the path to the input file for the given model name.

        :param model_name: name of the model to get the input file for
        :type model_name: str
        :return: path to the input file
        :rtype: Union[str, os.PathLike]
        """
        return os.path.join(self.inputs_folder, f"{model_name}", f"{model_name}.yaml")

    def get_data_model(self, model_name: str) -> FDM:
        """
        This method returns the data model for the given model name by reading the
        input file.

        :param model_name: name of the model to get the data model for
        :type model_name: str
        :return: data model
        :rtype: FDM
        """
        input_file_path = self.get_input_file_path(model_name)

        # Read and prepare the input file:
        fdm = FFs.read_data_from_yaml(input_file_path, FDM)

        if fdm.run.geometry is None:
            fdm.run.geometry = 1
        if fdm.run.mesh is None:
            fdm.run.mesh = 1
        if fdm.run.solution is None:
            fdm.run.solution = 1

        return fdm

    def run_fiqus(
            self,
            data_model: FDM,
            model_name: str,
            run_type: Literal[
                "start_from_yaml",
                "mesh_only",
                "geometry_only",
                "geometry_and_mesh",
                "pre_process_only",
                "mesh_and_solve_with_post_process_python",
                "solve_with_post_process_python",
                "solve_only",
                "post_process_getdp_only",
                "post_process_python_only",
            ],
    ) -> None:
        """
        This method runs FiQuS with the given model name and run type.

        :param model_name: name of the model to run FiQuS for
        :type model_name: str
        :param run_type: run type to run FiQuS with
        :type run_type: Literal[
                "start_from_yaml",
                "mesh_only",
                "geometry_only",
                "geometry_and_mesh",
                "pre_process_only",
                "mesh_and_solve_with_post_process_python",
                "solve_with_post_process_python",
                "solve_only",
                "post_process_getdp_only",
                "post_process_python_only",
            ]
        """
        # Make sure the run type is correct:
        data_model.run.type = run_type

        # Make sure the output files are overwritten:
        data_model.run.overwrite = True

        # Disable GUI:
        data_model.run.launch_gui = False

        # Prepare the output folder:
        model_folder = os.path.join(self.outputs_folder, f"{model_name}_{run_type}")
        FFs.prep_folder(model_folder)

        reference_geometry_folder = self.get_path_to_specific_reference_folder(
            data_model, model_name, folder="Geometry"
        )
        reference_mesh_folder = self.get_path_to_specific_reference_folder(
            data_model, model_name, folder="Mesh"
        )
        reference_solution_folder = self.get_path_to_specific_reference_folder(
            data_model, model_name, folder="Solution"
        )

        output_geometry_folder = self.get_path_to_specific_output_folder(
            data_model, model_name, run_type=run_type, folder="Geometry"
        )
        output_mesh_folder = self.get_path_to_specific_output_folder(
            data_model, model_name, run_type=run_type, folder="Mesh"
        )
        output_solution_folder = self.get_path_to_specific_output_folder(
            data_model, model_name, run_type=run_type, folder="Solution"
        )

        # Depending on the run_type, copy the reference files to the model folder:
        if run_type in ["geometry_only"]:
            pass  # do not copy anything
        elif run_type in ["mesh_only", 'mesh_and_solve_with_post_process_python']:
            shutil.copytree(
                reference_geometry_folder, output_geometry_folder, dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('Mesh*')
            )
        elif run_type in ["solve_only", "solve_with_post_process_python"]:
            shutil.copytree(
                reference_geometry_folder, output_geometry_folder, dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('Mesh*')
            )
            shutil.copytree(
                reference_mesh_folder, output_mesh_folder, dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('Solution*')
            )
        elif run_type in ['post_process_python_only', 'post_process_getdp_only']:
            shutil.copytree(
                reference_geometry_folder, output_geometry_folder, dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('Mesh*')
            )
            shutil.copytree(
                reference_mesh_folder, output_mesh_folder, dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('Solution*')
            )
            shutil.copytree(
                reference_solution_folder, output_solution_folder, dirs_exist_ok=True, ignore=None
            )
        else:  # "geometry_and_mesh", "start_from_yaml"
            raise ValueError(
                f"The test can not be run at the moment with run type set to {run_type}"
            )
        # Run FiQuS:
        if hasattr(self, "getdp_path"):
            MainFiQuS(
                model_folder=model_folder,
                input_file_path=self.get_input_file_path(model_name),
                fdm=data_model,
                GetDP_path=self.getdp_path
                # verbose=False,
            )
        else:
            MainFiQuS(
                model_folder=model_folder,
                input_file_path=self.get_input_file_path(model_name),
                fdm=data_model,
                # verbose=False,
            )

    def get_path_to_generated_file(
            self,
            data_model: FDM,
            model_name: str,
            file_name: str,
            file_extension: str,
            run_type: Literal[
                "start_from_yaml",
                "mesh_only",
                "geometry_only",
                "geometry_and_mesh",
                "pre_process_only",
                "mesh_and_solve_with_post_process_python",
                "solve_with_post_process_python",
                "solve_only",
                "post_process_getdp_only",
                "post_process_python_only",
            ],
            subfolder=None
    ) -> Union[str, os.PathLike]:
        """
        This method returns the path to the generated file with the given extension
        for the given model name depending on the run type.

        :param model_name: name of the model to get the generated file for
        :type model_name: str
        :param file_name: name of the file
        :type file_name: str
        :param file_extension: file extension of the generated file
        :type file_extension: str
        :param subfolder: additional folder inside specified 'folder'
        :type subfolder: str
        :param run_type: run type to run FiQuS with
        :type run_type: Literal[
                "start_from_yaml",
                "mesh_only",
                "geometry_only",
                "geometry_and_mesh",
                "pre_process_only",
                "mesh_and_solve_with_post_process_python",
                "solve_with_post_process_python",
                "solve_only",
                "post_process_getdp_only",
                "post_process_python_only",
            ]
        :return: path to the generated file
        :rtype: Union[str, os.PathLike]
        """
        if run_type == "geometry_only":
            folder = "Geometry"
        elif run_type == "mesh_only":
            folder = "Mesh"
        elif run_type == "solve_only":
            folder = "Solution"
        elif run_type == "solve_with_post_process_python":
            folder = "Solution"
        elif run_type == "post_process_python_only":
            folder = "Solution"
        else:
            raise ValueError(
                "The run type must be geometry_only, mesh_only, solve_only, solve_with_post_process_python, post_process_python_only!"
            )

        sections_folder = self.get_path_to_specific_output_folder(
            data_model, model_name, run_type, folder
        )

        if subfolder:
            generated_file = os.path.join(
                sections_folder, subfolder,
                f"{file_name}.{file_extension}",
            )
        else:
            generated_file = os.path.join(
                sections_folder,
                f"{file_name}.{file_extension}",
            )
        # Check if the file exists:
        if not os.path.isfile(generated_file):
            raise FileNotFoundError(
                f"Could not find the generated file: {generated_file}!"
            )

        return generated_file

    def get_path_to_specific_reference_folder(
            self,
            data_model: FDM,
            model_name: str,
            folder: Literal[
                "Geometry",
                "Mesh",
                "Solution",
            ],
    ):
        """
        This method returns the path to a specific reference folder (Geometry, Mesh, or
        Solution) for the given model name.

        :param model_name: name of the model to get the reference folder for
        :type model_name: str
        :param folder: folder to get the reference folder for
        :type folder: Literal[
                "Geometry",
                "Mesh",
                "Solution",
            ]
        """
        fdm = data_model
        geometry_folder_name = f"Geometry_{fdm.run.geometry}"
        mesh_folder_name = f"Mesh_{fdm.run.mesh}"
        solve_folder_name = f"Solution_{fdm.run.solution}"

        if folder == "Geometry":
            reference_folder = os.path.join(
                self.references_folder, model_name, geometry_folder_name
            )
        elif folder == "Mesh":
            reference_folder = os.path.join(
                self.references_folder,
                model_name,
                geometry_folder_name,
                mesh_folder_name,
            )
        elif folder == "Solution":
            reference_folder = os.path.join(
                self.references_folder,
                model_name,
                geometry_folder_name,
                mesh_folder_name,
                solve_folder_name,
            )

        return reference_folder

    def get_path_to_specific_output_folder(
            self,
            data_model: FDM,
            model_name: str,
            run_type: Literal[
                "start_from_yaml",
                "mesh_only",
                "geometry_only",
                "geometry_and_mesh",
                "pre_process_only",
                "mesh_and_solve_with_post_process_python",
                "solve_with_post_process_python",
                "solve_only",
                "post_process_getdp_only",
                "post_process_python_only",
            ],
            folder: Literal[
                "Geometry",
                "Mesh",
                "Solution",
            ],
    ):
        """
        This method returns a specific path (Geometry, Mesh, or Solution) to the output
        folder for the given model name depending on the run type.

        :param model_name: name of the model to get the output folder for
        :type model_name: str
        :param run_type: run type to run FiQuS with
        :type run_type: Literal[
                "start_from_yaml",
                "mesh_only",
                "geometry_only",
                "geometry_and_mesh",
                "pre_process_only",
                "mesh_and_solve_with_post_process_python",
                "solve_with_post_process_python",
                "solve_only",
                "post_process_getdp_only",
                "post_process_python_only",
            ]
        :param folder: folder to get the output folder for
        :type folder: Literal[
                "Geometry",
                "Mesh",
                "Solution",
            ]
        """
        fdm = data_model
        geometry_folder_name = f"Geometry_{fdm.run.geometry}"
        mesh_folder_name = f"Mesh_{fdm.run.mesh}"
        solve_folder_name = f"Solution_{fdm.run.solution}"

        if run_type is None:
            model_folder_name = model_name
        else:
            model_folder_name = f"{model_name}_{run_type}"

        if folder == "Geometry":
            output_folder = os.path.join(
                self.outputs_folder, model_folder_name, geometry_folder_name
            )
        elif folder == "Mesh":
            output_folder = os.path.join(
                self.outputs_folder,
                model_folder_name,
                geometry_folder_name,
                mesh_folder_name,
            )
        elif folder == "Solution":
            output_folder = os.path.join(
                self.outputs_folder,
                model_folder_name,
                geometry_folder_name,
                mesh_folder_name,
                solve_folder_name,
            )

        FFs.prep_folder(output_folder)

        return output_folder

    def get_path_to_reference_file(
            self,
            data_model: FDM,
            model_name: str,
            file_name: str,
            file_extension: str,
            folder: Literal[
                "Geometry",
                "Mesh",
                "Solution",
            ],
            subfolder=None
    ) -> Union[str, os.PathLike]:
        """
        This method returns the path to the reference file with the given extension
        for the given model name from the given folder.

        :param model_name: name of the model to get the reference file for
        :type model_name: str
        :param file_name: name of the model to get the reference file for
        :type file_name: str
        :param file_extension: file extension of the reference file
        :type file_extension: str
        :param folder: folder to get the reference file from
        :type folder: Literal[
                "Geometry",
                "Mesh",
                "Solution",
            ]
        :param subfolder: additional folder inside specified 'folder'
        :type subfolder: str
        :return: path to the reference file
        :rtype: Union[str, os.PathLike]
        """
        reference_folder = self.get_path_to_specific_reference_folder(
            data_model, model_name, folder=folder
        )
        if subfolder:
            reference_file = os.path.join(
                reference_folder, subfolder,
                f"{file_name}.{file_extension}", )
        else:
            reference_file = os.path.join(
                reference_folder,
                f"{file_name}.{file_extension}", )

        # Check if the file exists:
        if not os.path.isfile(reference_file):
            raise FileNotFoundError(
                f"Could not find the reference file: {reference_file}!"
            )

        return reference_file

    def compare_json_or_yaml_files(self, file_1, file_2, tolerance=0, excluded_keys=None):
        """
        This method compares the contents of two JSON or YAML files. It is used to
        check that the generated files are the same as the reference.

        :param file_1: path to the first file
        :type file_1: Union[str, os.PathLike]
        :param file_2: path to the second file
        :type file_2: Union[str, os.PathLike]
        :param tolerance: tolerance for numeric differences (default is 0)
        :type tolerance: int or float
        :param excluded_keys: keys to exclude from comparison (default is None)
        :type excluded_keys: List[str]
        """
        try:
            # YAML is a superset of JSON, so we can use the same parser for both:
            yaml = ruamel.yaml.YAML(typ="safe", pure=True)
            with open(file_1, "r") as file:
                file_1_dictionary = yaml.load(file)

            with open(file_2, "r") as file:
                file_2_dictionary = yaml.load(file)
        except:
            raise ValueError("The files must be JSON or YAML files!")

        # Remove excluded keys from both dictionaries
        if excluded_keys:
            file_1_dictionary = self._remove_excluded_keys(file_1_dictionary, excluded_keys)
            file_2_dictionary = self._remove_excluded_keys(file_2_dictionary, excluded_keys)

        # Compare the dictionaries:
        if tolerance == 0:
            self.assertDictEqual(
                file_1_dictionary,
                file_2_dictionary,
                msg=f"{file_1} did not match {file_2}!",
            )
        else:
            self.compare_dicts(file_1_dictionary, file_2_dictionary, tolerance)

    def compare_conductor_files(self, file_1, file_2, tolerance=0):
        """
        This method compares the contents of two JSON or YAML files. It is used to
        check that the generated files are the same as the reference.

        :param file_1: path to the first file
        :type file_1: Union[str, os.PathLike]
        :param file_2: path to the second file
        :type file_2: Union[str, os.PathLike]
        :param tolerance: tolerance for numeric differences (default is 0)
        :type tolerance: float
        """
        print('Comparing:')
        print(f'Output file: {file_1}')
        print(f'Reference file: {file_2}')
        file_1_dictionary = ParserCOND().read_cond(file_1)
        file_2_dictionary = ParserCOND().read_cond(file_2)

        # Compare the dictionaries:
        if tolerance == 0:
            self.assertDictEqual(
                file_1_dictionary,
                file_2_dictionary,
                msg=f"{file_1} did not match {file_2}!",
            )
        else:
            self.compare_dicts(file_1_dictionary, file_2_dictionary, tolerance)

    def _remove_excluded_keys(self, data, excluded_keys):
        """
        Recursively removes excluded keys from a dictionary.

        :param data: the dictionary to process
        :type data: dict
        :param excluded_keys: the keys to remove
        :type excluded_keys: List[str]
        :return: the dictionary without excluded keys
        :rtype: dict
        """
        if not isinstance(data, dict):
            return data  # Return non-dict types unchanged

        return {
            key: self._remove_excluded_keys(value, excluded_keys)
            for key, value in data.items()
            if key not in excluded_keys
        }

    def compare_dicts(self, dict1, dict2, tolerance):
        """
        This method compares the contents of two dictionaries, taking into account
        floating point precision issues.

        :param dict1: first dictionary to compare
        :type dict1: dict
        :param dict2: second dictionary to compare
        :type dict2: dict
        :param tolerance: tolerance for comparing floating point numbers
        :type tolerance: float
        """
        for key in dict1.keys():
            if key not in dict2:
                self.fail(f'Key "{key}" not in both {dict1} and {dict2}')
            if isinstance(dict1[key], dict):
                self.compare_dicts(dict1[key], dict2[key], tolerance)
            elif isinstance(dict1[key], float):  # To handle precision errors in floats
                if not np.isclose(dict1[key], dict2[key], atol=tolerance):
                    self.fail(f'Values for key {key} are not close: {dict1[key]} vs {dict2[key]}')
            elif isinstance(dict1[key], list):  # To handle precision errors in lists of floats
                if len(dict1[key]) != len(dict2[key]):
                    self.fail(f'Lists for key {key} are not the same length')
                for i in range(len(dict1[key])):
                    if isinstance(dict1[key][i], float):
                        if not np.isclose(dict1[key][i], dict2[key][i], atol=tolerance):
                            self.fail(
                                f'Values at index {i} for key {key} are not close: {dict1[key][i]} vs {dict2[key][i]}')
                    elif dict1[key][i] != dict2[key][i]:
                        self.fail(
                            f'Values at index {i} for key {key} are not equal: {dict1[key][i]} vs {dict2[key][i]}')
            else:
                if dict1[key] == dict2[key]:
                    pass
                elif isinstance(dict1[key], str):  # To handle precision errors in floats
                    if not np.isclose(float(dict1[key]), float(dict2[key]), atol=tolerance):
                        self.fail(f'Values for key {key} are not close: {float(dict1[key])} vs {float(dict2[key])}')
                else:
                    self.fail(f'Values for key {key} are not equal: {dict1[key]} vs {dict2[key]}')

    def compare_pkl_files(self, file_1, file_2):
        """
        This method compares the contents of two pkl files. It is used to check that the
        generated files are the same as the reference.

        :param file_1: path to the first file
        :type file_1: Union[str, os.PathLike]
        :param file_2: path to the second file
        :type file_2: Union[str, os.PathLike]
        """
        # Compare the pickle files:
        self.assertTrue(
            filecmp.cmp(file_1, file_2),
            msg=f"{file_1} did not match {file_2}!",
        )

    @staticmethod
    def filter_content(file_path, keywords, n):
        """
        Read a file and return its content as a string,
        excluding lines containing any of the specified keywords.
        It also skips the first n lines.
        This looping is slower than the filecmp.cmp method, but it is more flexible.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            # Skip the first N lines
            for _ in range(n):
                next(f, None)
            # Filter remaining lines
            return ''.join(line for line in f if not any(keyword in line for keyword in keywords))

    def compare_text_files(self, file_1, file_2, exclude_lines_keywords: list = None, exclude_first_n_lines: int = 0):
        """
        This method compares the contents of two files, normalizing the text to ignore
        whitespaces and line skips. It is used to check that the generated files are the
        same as the reference.

        :param file_1: path to the first file
        :type file_1: Union[str, os.PathLike]
        :param file_2: path to the second file
        :type file_2: Union[str, os.PathLike]
        :param exclude_lines_keywords: List of keywords to exclude lines containing them.
        :type exclude_lines_keywords: list
        :param exclude_first_n_lines: Number of lines to exclude from the top.
        :type exclude_first_n_lines: int
        """
        print(f'Comparing: {file_1} with {file_2}')
        if exclude_lines_keywords:
            # Normalize the content of both files
            normalized_content_1 = self._normalize_file_content(file_1, exclude_lines_keywords, exclude_first_n_lines)
            normalized_content_2 = self._normalize_file_content(file_2, exclude_lines_keywords, exclude_first_n_lines)

            # Split the normalized content into lines
            lines1 = normalized_content_1.splitlines()
            lines2 = normalized_content_2.splitlines()

            # Compare line by line and collect differences
            differences = []
            max_lines = max(len(lines1), len(lines2))
            for i in range(max_lines):
                line1 = lines1[i] if i < len(lines1) else "<No Line>"
                line2 = lines2[i] if i < len(lines2) else "<No Line>"
                if line1 != line2:
                    differences.append(
                        f"Line {i + 1}:\n  File 1: {line1[:100]}\n  File 2: {line2[:100]}"
                    )
                    break

            # If there are differences, include them in the assertion message
            if differences:
                diff_message = "\n".join(differences)
                self.assertEqual(
                    normalized_content_1,
                    normalized_content_2,
                    msg=f"{file_1} did not match {file_2}!\nDifferences:\n{diff_message[0:100]}"
                )
            else:
                print("Files match!")
        else:
            # Compare the files with a binary check
            self.assertTrue(
                filecmp.cmp(file_1, file_2),
                msg=f"{file_1} did not match {file_2}!",
            )

    def _normalize_file_content(self, file_path, exclude_lines_keywords, exclude_first_n_lines):
        """
        Normalize the content of a file by:
        - Removing extra spaces and tabs
        - Ignoring line breaks
        - Excluding lines with specific keywords
        - Skipping the first n lines

        :param file_path: Path to the file to normalize
        :type file_path: Union[str, os.PathLike]
        :param exclude_lines_keywords: List of keywords to exclude lines containing them.
        :type exclude_lines_keywords: list
        :param exclude_first_n_lines: Number of lines to exclude from the top.
        :type exclude_first_n_lines: int
        :return: Normalized content as a single string
        :rtype: str
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            # Skip the first n lines
            lines = f.readlines()[exclude_first_n_lines:]

        # Filter out lines containing any of the specified keywords
        if exclude_lines_keywords:
            lines = [line for line in lines if not any(keyword in line for keyword in exclude_lines_keywords)]

        # Normalize the lines by removing extra spaces and joining them into a single string
        normalized_content = ''.join(' '.join(line.split()) for line in lines)
        return normalized_content

    def compare_csv_files(self, file_1: Union[str, os.PathLike], file_2: Union[str, os.PathLike],
                          exclude_lines_keywords: List[str] = None, exclude_first_n_lines: int = 0,
                          tolerance: float = 0.0):
        """
        Compare two CSV files while allowing for numerical differences within a specified tolerance.

        :param file_1: Path to the first CSV file.
        :param file_2: Path to the second CSV file.
        :param exclude_lines_keywords: List of keywords; lines containing these will be excluded.
        :param exclude_first_n_lines: Number of lines to exclude from the top.
        :param tolerance: Acceptable numerical difference between corresponding values.
        """
        print(f'Comparing: {file_1} with {file_2}')

        # Read and filter files
        filtered_content1 = self._filter_csv_content(file_1, exclude_lines_keywords, exclude_first_n_lines)
        filtered_content2 = self._filter_csv_content(file_2, exclude_lines_keywords, exclude_first_n_lines)

        # Check that the number of lines match
        self.assertEqual(len(filtered_content1), len(filtered_content2),
                         msg=f"File lengths do not match: {len(filtered_content1)} vs {len(filtered_content2)}")

        for row1, row2 in zip(filtered_content1, filtered_content2):
            self.assertEqual(len(row1), len(row2), msg=f"Row lengths do not match: {row1} vs {row2}")
            for val1, val2 in zip(row1, row2):
                if self._is_number(val1) and self._is_number(val2):
                    if np.isnan(float(val1)) and np.isnan(float(val2)):
                        continue  # Consider NaN values as equal
                    self.assertTrue(np.isclose(float(val1), float(val2), atol=tolerance),
                                    msg=f"Values {val1} and {val2} differ beyond tolerance {tolerance} for file {file_1} and {file_2}")
                else:
                    self.assertEqual(val1, val2, msg=f"String values do not match: {val1} vs {val2}")

    def _filter_csv_content(self, file_path, exclude_lines_keywords, exclude_first_n_lines):
        """Helper method to read CSV file and filter lines based on keywords and line numbers."""
        with open(file_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            content = [row for i, row in enumerate(reader)
                       if i >= exclude_first_n_lines and
                       (not exclude_lines_keywords or not any(kw in ','.join(row) for kw in exclude_lines_keywords))]
        return content

    def _is_number(self, value):
        """Helper method to check if a value is a number."""
        try:
            float(value)
            return True
        except ValueError:
            return False


class FiQuSGeometryTests(BaseClassesForTests):
    def generate_geometry(
            self,
            data_model: FDM,
            model_name: str,
    ) -> Tuple[Union[str, os.PathLike], Union[str, os.PathLike]]:
        """
        This method generates the geometry for the given model name.

        :param data_model: data model to run FiQuS with
        :type data_model: FDM
        :param model_name: name of the model to generate the geometry for
        :type model_name: str
        :return: path to the generated geometry and volume information files
        :rtype: Tuple[Union[str, os.PathLike], Union[str, os.PathLike]]
        """
        self.run_fiqus(data_model, model_name, "geometry_only")
        self.model_name = model_name

    def compare_number_of_entities(
            self,
            geometry_file_1: Union[str, os.PathLike],
            geometry_file_2: Union[str, os.PathLike],
    ):
        """
        This method compares the number of entities for each dimension in two geometry
        files. It is used to check that the generated geometry file is the same as the
        reference.

        :param geometry_file_1: path to the first geometry file
        :type geometry_file_1: Union[str, os.PathLike]
        :param geometry_file_2: path to the second geometry file
        :type geometry_file_2: Union[str, os.PathLike]
        """
        # Initialize gmsh:
        gmsh_utils = GmshUtils(verbose=False)
        gmsh_utils.initialize(verbosity_Gmsh=0)

        # Open the geometry files and get the entities:
        model_entities = {}
        for geometry_file in [geometry_file_1, geometry_file_2]:
            model_entities[geometry_file] = []

            gmsh.open(geometry_file)
            for dim in range(4):
                model_entities[geometry_file].append(
                    sorted(gmsh.model.getEntities(dim=dim))
                )
            gmsh.clear()

        # Compare the number of entities for each dimension:
        for dim in [0, 1, 2, 3]:
            self.assertEqual(
                len(model_entities[geometry_file_1][dim]),
                len(model_entities[geometry_file_2][dim]),
                msg=f"{geometry_file_1} and {geometry_file_2} did not match!",
            )

    def get_path_to_generated_file(
            self, data_model: FDM, model_name: str, file_extension: str
    ) -> Union[str, os.PathLike]:
        return super().get_path_to_generated_file(
            data_model,
            self.model_name,
            model_name,
            file_extension,
            run_type="geometry_only",
        )

    def get_path_to_reference_file(
            self, data_model: FDM, model_name: str, file_extension: str
    ) -> Union[str, os.PathLike]:
        return super().get_path_to_reference_file(
            data_model, self.model_name, model_name, file_extension, folder="Geometry"
        )


class FiQuSMeshTests(BaseClassesForTests):
    def generate_mesh(
            self,
            data_model: FDM,
            model_name: str,
    ) -> Tuple[Union[str, os.PathLike], Union[str, os.PathLike]]:
        """
        This method generates the mesh for the given model name.

        :param data_model: data model to run FiQuS with
        :type data_model: FDM
        :param model_name: name of the model to generate the mesh for
        :type model_name: str
        """
        self.run_fiqus(data_model, model_name, "mesh_only")
        self.model_name = model_name

    def compare_mesh_qualities(
            self, mesh_file_1: Union[str, os.PathLike], mesh_file_2: Union[str, os.PathLike]
    ):
        """
        This method compares the mesh qualities of two mesh files. It is used to check
        that the generated mesh file is the same as the reference.

        :param mesh_file_1: path to the first mesh file
        :type mesh_file_1: Union[str, os.PathLike]
        :param mesh_file_2: path to the second mesh file
        :type mesh_file_2: Union[str, os.PathLike]
        """
        # Initialize gmsh:
        gmsh_utils = GmshUtils(verbose=False)
        gmsh_utils.initialize(verbosity_Gmsh=0)

        # Open the mesh files and get the average mesh quality:
        average_mesh_qualities = []
        for mesh_file in [mesh_file_1, mesh_file_2]:
            # Get physical group names:
            mesh = ParserMSH(mesh_file)
            average_mesh_qualities.append(mesh.get_average_mesh_quality())

        # Make sure the average mesh qualities are close enough:
        ratio = min(average_mesh_qualities) / max(average_mesh_qualities)
        self.assertGreater(
            ratio,
            0.9,
            msg=f"{mesh_file_1} and {mesh_file_2} did not match!",
        )

    def get_path_to_generated_file(
            self, data_model, model_name: str, file_extension: str
    ) -> Union[str, os.PathLike]:
        return super().get_path_to_generated_file(
            data_model, self.model_name, model_name, file_extension, run_type="mesh_only"
        )

    def get_path_to_reference_file(
            self, data_model, model_name: str, file_extension: str
    ) -> Union[str, os.PathLike]:
        return super().get_path_to_reference_file(
            data_model, self.model_name, model_name, file_extension, folder="Mesh"
        )


class FiQuSSolverTests(BaseClassesForTests):
    def solve(
            self,
            data_model: FDM,
            model_name: str,
            run_type: str = "solve_only"
    ) -> Tuple[Union[str, os.PathLike], Union[str, os.PathLike]]:
        """
        This method solves the given model name.

        :param data_model: data model to run FiQuS with
        :type data_model: FDM
        :param model_name: name of the model to generate the mesh for
        :type model_name: str
        """
        self.run_fiqus(data_model, model_name, run_type)
        self.model_name = model_name

    def compare_pos_files(
            self, pos_file_1: Union[str, os.PathLike], pos_file_2: Union[str, os.PathLike],
            rel_tolerance: float = 1e-10, abs_tolerance: float = 0.0, n_top_values_only: int = 0
    ):
        """
        This method compares the contents of two pos files. It is used to check that
        the generated pos file is the same as the reference.

        :param pos_file_1: path to the first pos file
        :type pos_file_1: Union[str, os.PathLike]
        :param pos_file_2: path to the second pos file
        :type pos_file_2: Union[str, os.PathLike]
        :param rel_tolerance: relative tolerance
        :type rel_tolerance: float
        :param abs_tolerance: absolute tolerance
        :type abs_tolerance: float
        :param n_top_values_only: if > 0 then the number of top n values is compared
        :type n_top_values_only: int
        """
        # Initialize gmsh:
        gmsh_utils = GmshUtils(verbose=False)
        gmsh_utils.initialize(verbosity_Gmsh=0)

        # Open the pos files and get the model data:
        model_datas = []
        time_steps = [0, 0]
        for idx, pos_file in enumerate([pos_file_1, pos_file_2]):
            # remove all old views
            gmsh.clear()
            # Open the pos file:
            gmsh.open(pos_file)
            data_all_steps = []

            while True:
                # Save all available time steps up to 100:
                try:
                    (
                        data_type,
                        tags,
                        data,
                        time,
                        numComponents,
                    ) = gmsh.view.getHomogeneousModelData(tag=0, step=time_steps[idx])
                    data_all_steps.extend(list(data))
                    time_steps[idx] += 1  # Move to the next time step
                except:
                    print(f"Finished reading {pos_file} at time step {time_steps[idx]}.")
                    break

            model_datas.append(data_all_steps)

        # Make sure the number of time steps are the same:
        self.assertEqual(
            time_steps[0],
            time_steps[1],
            msg=f"{pos_file_1} and {pos_file_2} do not have the same number of time steps!",
        )

        # Make sure the pos files are the same length:
        self.assertEqual(
            len(model_datas[0]),
            len(model_datas[1]),
            msg=f"{pos_file_1} and {pos_file_2} are not the same length!",
        )

        # Convert to numpy arrays:
        if n_top_values_only > 0:
            print(f"Only top {n_top_values_only} values are compared.")
            model_data1 = np.sort(np.partition(np.array(model_datas[0]), -n_top_values_only)[-n_top_values_only:])
            model_data2 = np.sort(np.partition(np.array(model_datas[1]), -n_top_values_only)[-n_top_values_only:])
            data = np.column_stack((model_data1, model_data2))

            csv_path = f"{os.path.splitext(pos_file_1)[0]}.csv"
            print(f'Saving {csv_path}')
            # np.savetxt(csv_path, data, delimiter=",", header="pos_file_1,pos_file_2", comments='')
        else:
            model_data1 = np.array(model_datas[0])
            model_data2 = np.array(model_datas[1])

        # Compare the data:
        np.testing.assert_allclose(
            model_data1,
            model_data2,
            rtol=rel_tolerance,
            atol=abs_tolerance,
        )

    def get_path_to_generated_file(
            self, data_model, model_name: str, file_extension: str, subfolder=None, run_type="solve_only"
    ) -> Union[str, os.PathLike]:
        return super().get_path_to_generated_file(
            data_model,
            self.model_name,
            model_name,
            file_extension,
            run_type=run_type,
            subfolder=subfolder
        )

    def get_path_to_reference_file(
            self, data_model, model_name, file_extension, subfolder=None
    ) -> Union[str, os.PathLike]:
        return super().get_path_to_reference_file(
            data_model, self.model_name, model_name, file_extension, folder="Solution", subfolder=subfolder
        )


class FiQuSPostProcessPythonTests(BaseClassesForTests):
    def post_process_python(
            self,
            data_model: FDM,
            model_name: str,
    ) -> Tuple[Union[str, os.PathLike], Union[str, os.PathLike]]:
        """
        This method postprocess with python the given model name.

        :param data_model: data model to run FiQuS with
        :type data_model: FDM
        :param model_name: name of the model to generate the mesh for
        :type model_name: str
        """
        self.run_fiqus(data_model, model_name, "post_process_python_only")
        self.model_name = model_name

    def get_path_to_generated_file(
            self, data_model, model_name: str, file_extension: str, subfolder=None
    ) -> Union[str, os.PathLike]:
        return super().get_path_to_generated_file(
            data_model,
            self.model_name,
            model_name,
            file_extension,
            subfolder=subfolder,
            run_type="post_process_python_only",
        )

    def get_path_to_reference_file(
            self, data_model, model_name, file_extension, subfolder=None
    ) -> Union[str, os.PathLike]:
        return super().get_path_to_reference_file(
            data_model, self.model_name, model_name, file_extension, folder="Solution", subfolder=subfolder
        )