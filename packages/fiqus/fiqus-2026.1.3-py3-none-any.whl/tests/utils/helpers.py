import functools
import itertools
import operator
import os
import unittest
from typing import List

import numpy as np

from fiqus.data.DataFiQuS import FDM
from fiqus.utils.Utils import FilesAndFolders as FFs


class Paths:
    """
    Helper class used in FiQuS tests to get file and folder paths
    :param model_name: name of yaml input file (without .yaml)
    :param f_extension: file extension to apply to the folders, for example '.brep' or '.msh'
    :return: tuple: fdm, outputs_folder, input_folder, input_file, model_folder, model_file, reference_folder, reference_file
    """

    def __init__(self, model_name, f_extension=''):
        self.inputs_folder_name = '_inputs'
        self.outputs_folder_name = '_outputs'
        self.references_folder_name = '_references'

        self.test_outputs_folder = os.path.join(os.getcwd(), self.outputs_folder_name)
        self.inputs_folder = os.path.join(os.getcwd(), self.inputs_folder_name, model_name)
        self.model_folder = os.path.join(os.getcwd(), self.outputs_folder_name, model_name)
        self.references_folder = os.path.join(os.getcwd(), self.references_folder_name, model_name)

        self.input_file = os.path.join(self.inputs_folder, f'{model_name}.yaml')
        self.model_file = os.path.join(self.model_folder, f'{model_name}.{f_extension}')
        self.reference_file = os.path.join(self.references_folder, f'{model_name}.{f_extension}')
        self.reference_vi_file = os.path.join(self.references_folder, f'{model_name}.vi')
        self.reference_geo_yaml_file = os.path.join(self.references_folder, f'geometry.yaml')
        self.reference_mesh_yaml_file = os.path.join(self.references_folder, f'mesh.yaml')
        self.reference_regions_file = os.path.join(self.references_folder, f'{model_name}.regions')


def filecmp(filename1, filename2):
    """
    From: https://stackoverflow.com/questions/254350/in-python-is-there-a-concise-way-of-comparing-whether-the-contents-of-two-text
    Do the two files have exactly the same contents?
    """
    with open(filename1, "rb") as fp1, open(filename2, "rb") as fp2:
        print(f'The {filename1} size is: {os.fstat(fp1.fileno()).st_size} b')
        print(f'The {filename2} size is: {os.fstat(fp2.fileno()).st_size} b')
        if os.fstat(fp1.fileno()).st_size != os.fstat(fp2.fileno()).st_size:
            return False  # different sizes ∴ not equal

        # set up one 4k-reader for each file
        fp1_reader = functools.partial(fp1.read, 4096)
        fp2_reader = functools.partial(fp2.read, 4096)

        # pair each 4k-chunk from the two readers while they do not return '' (EOF)
        cmp_pairs = zip(iter(fp1_reader, b''), iter(fp2_reader, b''))

        # return True for all pairs that are not equal
        inequalities = itertools.starmap(operator.ne, cmp_pairs)
        ineqs = []
        for ineq in inequalities:
            ineqs.append(ineq)
        # voila; any() stops at first True value
        print(f'The file comp function gives: {not any(inequalities)}')
        return not any(inequalities)


def assert_two_parameters(true_value, test_value):
    """
     Some functions used in multiple test functions
        **Assert two parameters - accepts multiple types**
    """
    # TODO: improve robustness and readability
    test_case = unittest.TestCase()

    if isinstance(true_value, np.ndarray) or isinstance(true_value, list):
        if len(true_value) == 1:
            true_value = float(true_value)

    if isinstance(test_value, np.ndarray) or isinstance(test_value, list):
        if len(test_value) == 1:
            test_value = float(test_value)

    # Comparison
    if isinstance(test_value, np.ndarray) or isinstance(test_value, list):
        if np.array(true_value).ndim == 2:
            for i, test_row in enumerate(test_value):
                if isinstance(test_row[0], np.floating):
                    test_row = np.array(test_row).round(10)
                    true_value[i] = np.array(true_value[i]).round(10)

                test_case.assertListEqual(list(test_row), list(true_value[i]))
        else:
            if isinstance(test_value[0], np.floating):
                test_value = np.array(test_value).round(10)
                true_value = np.array(true_value).round(10)

            test_case.assertListEqual(list(test_value), list(true_value))
    else:
        test_case.assertEqual(test_value, true_value)


def assert_equal_readable_files(file1: str, file2: str, verbose: bool = False) -> None:
    """
    Assert that two readable (e.g. csv or cond) files are equal
    :param file1: full path to the first file
    :type file1: str
    :param file2: full path to the second file
    :type file2: str
    :param verbose: if ture more is printed to the output
    :type verbose: bool
    :return: Nothing, however it asserts using unittest testcase
    :rtype: None
    """
    test_case = unittest.TestCase()

    # Load files to compare
    with open(file1, "r") as f1, open(file2, "r") as f2:
        file1 = f1.readlines()
        file2 = f2.readlines()

    flag_equal = True
    for line in file2:
        if line not in file1:
            if verbose:
                print(f"Found line that appears in File2 but not in File1: {line}")
            flag_equal = False
    for line in file1:
        if line not in file2:
            if verbose:
                print(f"Found line that appears in File1 but not in File2: {line}")
            flag_equal = False

    # Display message and assert files have the same entries
    if flag_equal:
        if verbose:
            print('Files {} and {} have the same entries.'.format(file1, file2))
    test_case.assertEqual(flag_equal, True)


def compare_conductors_dicts(dict1, dict2, max_relative_error=1e-6):
    """
    Function that compares two conductor dicts and returns message list describing differences
    If there are no differences the list is empty
    :param dict1: reference dict to compare
    :param dict2: output dict to compare
    :param max_relative_error: maximum relative difference of values

    """

    the_same_flag = True
    for brick_id in dict1.keys():
        if dict1[brick_id] != dict2[brick_id]:
            pass
        else:
            for key, value1 in dict1[brick_id].items():
                value2 = dict2[brick_id][key]
                if key in ['SHAPE', 'DRIVELABEL']:
                    if value1 == value2:
                        pass
                    else:
                        the_same_flag = False
                else:
                    if abs(float(value1) - float(value2)) < max_relative_error * float(value2):
                        pass
                    elif float(value1) == float(value2):  # both zero
                        pass
                    else:
                        the_same_flag = False

    return the_same_flag
