# -*- coding: utf-8 -*-
"""
This submodule will parse the raw excel/csv/text files into pandas dataframes
first. Before another module will extract from the dataframes and load into
the database

@author Declan Valters
"""

import os
import re
import warnings
import pandas as pd


dataframes = {}

# Names of soil sheets in the Soils directory
SOILS_SUBTABLES = ('Moisture', 'ResinExtracts', 'pH', 'NitrateAmmonia')

# Expected names of ancil data
ANCIL_DATA_NAMES = ('Fluorescence', 'GS', 'Harvest', 'CN', 'HI', 'Height',
                    'LAI', 'SPAD', 'ThetaProbe',
                    'NitrateAmmonia', 'ResinExtracts', 'Moisture', 'pH')

DUMMY_PICO_SPECTRA = """{    
 "SequenceNumber": 0, 
 "Spectra": [
  {
   "Metadata": {
    "Batch": 0, 
    "Dark": false, 
    "Datetime": "2000-01-00T00:00:00.000000Z", 
    "Direction": "none", 
    "IntegrationTime": 0.0, 
    "IntegrationTimeUnits": "none", 
    "NonlinearityCorrectionCoefficients": [0], 
    "OpticalPixelRange": [0], 
    "Run": "dummy", 
    "SaturationLevel": 0, 
    "SerialNumber": "QEP01651", 
    "TemperatureDetectorActual": 0.0, 
    "TemperatureDetectorSet": 0.0, 
    "TemperatureHeatsink": null, 
    "TemperatureMicrocontroller": 0.0, 
    "TemperaturePCB": 0.0, 
    "TemperatureUnits": "degrees Celcius", 
    "Type": "light", 
    "WavelengthCalibrationCoefficients": [0], 
    "name": "none"
   },
   "Pixels": [0] }}"""

def file_and_dict_name(datadir, curdirname, fname):
    filefullname = os.path.join(curdirname, fname)
    # Get a list of the subdirs, then get the field name folder
    # subtract dirname rfom directory!
    parentdirs = os.path.commonprefix([datadir, curdirname])
    enddir = curdirname.split(parentdirs)[1]
    site_code = enddir.split(os.path.sep)[2]

    # Take off the year bit, as it is also in the filename later
    site_code = site_code[:-4]
    dictname = site_code + os.path.splitext(os.path.basename(fname))[0]
    return (filefullname, dictname)


def extract_dataframes(directory):
    for (dirname, subdirs, files) in os.walk(directory):
        for fname in files:
            # Only match "xlsx" files, exclude recovery/backup files
            if re.match("^(?![~$]).*.xlsx$", fname):
                # Could be try blocks here:
                try:
                    extract_excel_format(*file_and_dict_name(directory, dirname, fname))
                except ImportError:
                    print("You must have the xlrd python module installed"
                          "...Skipping " + fname)
            if re.match("^(?![~$]).*.PRN$", fname):
                extract_PRN_format(*file_and_dict_name(directory, dirname, fname))
    return dataframes


def extract_excel_format(filefullname, dictname):
    dataframes[dictname] = pd.read_excel(filefullname, skiprows=1)
    if 'Fluorescence' in dictname:
        upper_header = pd.MultiIndex.from_product(
            [['Sample1', 'Sample2',
                'Sample3', 'Sample4', 'Sample5', 'PlotAverage'],
                ['Fo', 'Fv', 'Fm', 'Fv/Fm', 'Fv/Fo']])
        new_header = dataframes[dictname].columns[0:3].union(upper_header)
        dataframes[dictname].columns = new_header
    if dictname in dataframes:
        # Perhaps log as well if duplicate
        warnings.warn("always", UserWarning)
    else:
        dataframes[dictname] = pd.read_excel(filefullname, skiprows=1)


def extract_csv_format(filefullname, dictname):
    if dictname in dataframes:
        # Perhaps log as well if duplicate
        warnings.warn("always", UserWarning)
    else:
        dataframes[dictname] = pd.read_csv(filefullname, skiprows=1)


def extract_PRN_format(filefullname, dictname):
    """This is the raw text file format that comes of the machine"""
    if dictname != "TEST_PRN_dict" and dictname in dataframes:
        # Perhaps log as well if duplicate
        warnings.warn("always", UserWarning)
    else:
        # Build dataframe manually using the generator.
        PRN_dataframe = pd.DataFrame(columns=['Time', 'Plot', 'Sample',
                                              'Transmitted', 'Spread',
                                              'Incident',
                                              'Beam Frac', 'Zenith',  'LAI'])
        for i, line in enumerate(generate_goodPRNline(filefullname)):
            PRN_dataframe.loc[i] = line.split()
        PRN_dataframe = PRN_dataframe.apply(pd.to_numeric, errors='ignore')
        dataframes[dictname] = PRN_dataframe


def generate_goodPRNline(filename):
    """Generator that yields a data line from the PRN file"""
    with open(filename) as f:
        for line in f:
            if line[0].isdigit() and ':' in line:
                yield line


def get_date_from_df_key(df):
    return df.split('_')[2]


# I don't think this function should go in this module, but ok for now...
def generate_dummy_spectra_for_ancil(dataframes):
    """
    Logic:
      Dummy pico file created from plot name (and date?)
      but plot name is in the pandas dataframe from each ancil.
      So, loop through each dataframe, pop off the date and append it to
      the first row plot name - this is your dummy spectra name for the
      dummy pico file to write out.
    """
    plot_ids = set()
    pico_dir = "./picotest/"
    
    if not os.path.isdir(pico_dir):
        os.mkdir(pico_dir)

    for df in dataframes:
        # Get the date from the first part of the dict name before the '_'
        if 'LAI' in df:  # Odd format from PRN files
            break
        datestr = get_date_from_df_key(df)
        for index, row in dataframes[df].iterrows():
            # Row should have the plot name
            plot_id_name = row[0] + '_' + datestr
            plot_ids.add(plot_id_name)
            
            dummy_pico_name = plot_id_name + ".pico"
            # Don't create new dummy files if ones alreadt exist!
            if not os.path.exists(pico_dir + dummy_pico_name):
                # Write a new dummy pico file
                with open(pico_dir + dummy_pico_name, "w") as dummypico:
                    dummypico.writelines(DUMMY_PICO_SPECTRA)
        
    


def extract_PRN_header_info():
    pass


def read_PRN_to_dataframe():
    pass


class PRNdata(object):
    """Class that defines the data in a PRN file"""
    pass
