import collections
import os
import collections
from pathlib import Path
import pandas as pd
import os
import sys
import optparse


"""
Algorithm:

Parse and collect data from .txt file of PCP raw data, output a .csv file.

1. Group files based on its name, for example, 1-P.txt should be grouped with 1-S.txt
2. Extract data from a tuple/group of files(use different approach based on S/P file)
3. Merge all extracted data into one big excel/csv file

Usage eg:  python PCP_Transform.py path/to/your/work/directory outputfilename   

UI: 
    1. dialog -> select the working folder -> ask for Customized filename, e.g. 
    
TODO:
    1. Implement for saving the file into the working directory (network drive)
"""

"""Utility functions"""


def get_file_extension(filename: str):
    return Path(filename).suffix.lower()


def get_field_prefix(fileName: str) -> str:
    return fileName.split("-")[0]


def get_filed_sub(fileName: str) -> str:
    return fileName[2:3]


def strip_lines(lines: list[str]) -> list[list]:
    return [x.strip().split('\t') for x in lines]


def tuple_to_dict(list_of_tuple: list[tuple], d: dict) -> dict:
    for (x, y) in list_of_tuple:
        d.setdefault(x, []).append(y)
    return d



def get_first_five_cols(lines: list[str], num_rows: int) -> pd.DataFrame:
    """
    Function to generate information from the file and generate the first five columns(general information of mice),
    the result is like the following:

    Protocol,Steps,Channels,Animal # ,Study Name
    PCP Photopic Adapted Long Protocol06 [14806-D  ||  ECN 1496  ||  8 June 2020],5,4,6137-B,OM-243_C2

    """

    # Read data in the file
    d = collections.defaultdict(list)
    protocol_name = lines[14].strip().split('\t')
    steps = lines[18].strip().split('\t')
    channel = lines[19].strip().split('\t')
    animal_number = lines[20].strip().split('\t')
    study_name = lines[21].strip().split('\t')

    # Make n copy of data read above
    d[protocol_name[0]].extend([protocol_name[1]] * num_rows)
    d[steps[0]].extend([steps[1]] * num_rows)
    d[channel[0]].extend([channel[1]] * num_rows)
    d[animal_number[0]].extend([animal_number[1]] * num_rows)
    d[study_name[0]].extend([study_name[1]] * num_rows)
    df = pd.DataFrame.from_dict(d)

    return df


# Function to group files based on their names, e.g 1-P.txt and 1-S.txt will be grouped together because they both
# have '1' as prefix
def organize_files(path: str) -> dict:
    if not os.path.isdir(path):
        print(f"{path} is not a directory")
        return {}

    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    file_dict = collections.defaultdict(list)
    for file in files:
        extention = get_file_extension(file)
        if extention != ".txt":
            continue
        file_key = get_field_prefix(file)
        group = file_dict.get(file_key, [])
        group.append(file)
        file_dict[file_key] = group

    return file_dict


# Function to read data from files
def parse_file(filename, file_type, workspace) -> pd.DataFrame:
    os.chdir(workspace)

    with open(filename, "r", encoding='utf-8',
              errors='ignore') as f:
        lines = f.readlines()
        columns = lines[26].strip().split()

        # Reformat the column name of 'Cage #'
        columns.remove('#')
        columns[2] = 'Cage #'

        if file_type == "P":
            num_rows = len(lines[27:47])
            first_five_cols = get_first_five_cols(lines, num_rows)
            # get data in marker's table section
            temp = strip_lines(lines[27:47])
            marker_table_data = pd.DataFrame.from_records(temp, columns=columns)
            res = pd.concat([first_five_cols, marker_table_data], axis=1)
            return res

        elif file_type == "S":
            num_rows = len(lines[27:62])
            first_five_cols = get_first_five_cols(lines, num_rows)
            # get data in marker's table section
            temp = strip_lines(lines[27:62])
            marker_table_data = pd.DataFrame.from_records(temp, columns=columns)
            res = pd.concat([first_five_cols, marker_table_data], axis=1)
            return res


def transform(file_groups: dict, workspace, outputFileName) -> None:
    if not file_groups:
        return []

    result = []
    for prefix, files in file_groups.items():
        files = sorted(files, key=get_filed_sub)
        p_file, s_file = files[0], files[1]

        # Read and aggregate data
        df_1 = parse_file(p_file, "P", workspace)
        df_2 = parse_file(s_file, "S", workspace)
        df = pd.concat([df_1, df_2], ignore_index=True)
        result.append(df)

    # Write data to the file
    final_data = pd.concat(result, ignore_index=True)
    final_data.to_csv(outputFileName)



def main():

    #Parse the coomand line argument
    parser = optparse.OptionParser()
    parser.add_option('-d', dest = 'directory',
                      type = 'str', 
                      help = 'path to the directory you want to work with')
    parser.add_option('-f', dest = 'filename',
                      type = 'str', 
                      help = 'desired name of your outputfile, be sure to include .csv at the end')

    options, args = parser.parse_args() 
    if (options.directory == None):
        print("You must provide a work directory.")
        print(parser.usage)
        exit(0)

    if (options.filename == None):
        print("You must provide a work directory.")
        print(parser.usage)
        exit(0)
        
    workspace = options.directory
    outputFileName = options.filename

     # Collect data from files
    file_groups = organize_files(path=workspace)
    transform(file_groups=file_groups, workspace=workspace, outputFileName=outputFileName)
    print("Process finished")
    

if __name__ == "__main__":
    main()

   
    