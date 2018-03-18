# -*- coding: utf-8 -*-
"""
This submodule will parse the raw excel/csv/text files into pandas dataframes
first. Before another module will extract from the dataframes and load into
the database
"""

import os
import re
import unittest
import pandas as pd

DATADIR = "/home/dvalters/Projects/SPECCHIO/DATA/"

TEST_PRN_DIR = ("/home/dav/SPECCHIO-QGIS-python/DATA/ES/field_scale/"
                "ES_F1_2017/plot_scale_data/LAI/")

dataframes = {}


def file_and_dict_name(dirname, fname):
    filefullname = os.path.join(dirname, fname)
    dictname = os.path.splitext(os.path.basename(fname))[0]
    return (filefullname, dictname)


def extract_dataframes():
    for (dirname, subdirs, files) in os.walk(DATADIR):
        # print('[' + dirname + ']')
        for fname in files:
            # Only match "xlsx" files, exclude recovery/backup files
            if re.match("^(?![~$]).*.xlsx$", fname):
                # Could be try blocks here:
                extract_excel_format(*file_and_dict_name(dirname, fname))
            if re.match("^(?![~$]).*.PRN$", fname):
                extract_PRN_format(*file_and_dict_name(dirname, fname))
    return dataframes


def extract_excel_format(filefullname, dictname):
    dataframes[dictname] = pd.read_excel(filefullname, skiprows=1)


def extract_csv_format(filefullname, dictname):
    dataframes[dictname] = pd.read_csv(filefullname, skiprows=1)


def extract_PRN_format(filefullname, dictname):
    """This is the raw text file format that comes of the machine"""
    # Build dataframe manually using the generator.
    PRN_dataframe = pd.DataFrame(columns=['Time', 'Plot', 'Sample',
                                          'Transmitted', 'Spread',  'Incident',
                                          'Beam Frac', 'Zenith',  'LAI'])
    for i, line in enumerate(generate_goodPRNline(filefullname)):
        PRN_dataframe.loc[i] = line.split()
    dataframes[dictname] = PRN_dataframe


def generate_goodPRNline(filename):
    """Generator that yields a data line from the PRN file"""
    with open(filename) as f:
        for line in f:
            if line[0].isdigit() and ':' in line:
                yield line


def read_PRN_to_dataframe():
    pass


class PRNdata(object):
    """Class that defines the data in a PRN file"""
    pass


class TestParser(unittest.TestCase):

    def test_correct_files_parsed(self):

        BAD_STRINGS = ['$', '~', 'csv', 'xls']

        dfs = extract_dataframes()
        # Could be the other way round I suppose...
        for bad_string in BAD_STRINGS:
            self.assertFalse(any(bad_string in key for key in dfs.keys()))

    def test_PRN_parsing_columns(self):
        """PRN data should have nine columns if correctly ingested"""
        filefullname = TEST_PRN_DIR + "20170714_LAI.PRN"
        extract_PRN_format(filefullname, "TEST_PRN_dict")
        self.assertEquals(len(dataframes['TEST_PRN_dict'].columns), 9)

    def test_generate_PRN_lines(self):
        """Test that we can strip and print the PRN text file lines """
        reader = generate_goodPRNline(TEST_PRN_DIR + "20170714_LAI.PRN")
        while True:
            try:
                print(next(reader))
            except StopIteration:
                break

if __name__ == '__main__':
    unittest.main()
