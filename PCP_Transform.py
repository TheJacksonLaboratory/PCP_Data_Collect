import collections
import os
import collections
import logging
import sys
from pathlib import Path
import requests
import pandas as pd
import mysql.connector as mysql
import datetime
import json
from base64 import b64encode
import os
import re
import yaml

"""
Algorithm:

1. Group files based on its name, for example, 1-P.txt should be grouped with 1-S.txt
2. Extract data from a tuple/group of files(use different approach based on S/P file)
3. Merge all extracted data into one big excel/csv file

TODO 09/29/2023

1. Find a way to get line number of errors
2. Add logger to script
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


def basic_auth(az_username, access_token):
    token = b64encode(f"{az_username}:{access_token}".encode('utf-8')).decode("ascii")
    return f'Basic {token}'


# Function to create a new PBI on Azure DevOps board
def create_work_item(message: str, az_username:str):
    url = "https://dev.azure.com/jacksonlaboratory/teams/_apis/wit/workitems/$Bug?api-version=7.0"
    payload = json.dumps(
        [
            {
                "op": "add",
                "path": "/fields/System.Title",
                "from": None,
                "value": "Errors detected in PCP data collecting"
            },
            {
                "op": "add",
                "path": "/fields/System.State",
                "from": None,
                "value": "New"
            },
            {
                "op": "add",
                "path": "/fields/System.History",
                "from": None,
                "value": message
            },
            {
                "op": "add",
                "path": "/fields/System.AssignedTo",
                "from": None,
                "value": az_username
            },
            {
                "op": "add",
                "path": "/fields/System.AreaPath",
                "from": None,
                "value": "Teams\\Research\\KOMP"
            }
        ]
    )
    headers = {
        'Content-Type': 'application/json-patch+json',
        'Authorization': basic_auth(),
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.status_code)


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
def parse_file(filename, file_type) -> pd.DataFrame:
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


def transform(file_groups: dict) -> list[pd.DataFrame]:
    if not file_groups:
        return []

    result = []
    for prefix, files in file_groups.items():
        files = sorted(files, key=get_filed_sub)
        p_file, s_file = files[0], files[1]

        # Read and aggregate data from files
        df_1 = parse_file(p_file, "P")
        df_2 = parse_file(s_file, "S")
        df = pd.concat([df_1, df_2], ignore_index=True)
        result.append(df)

    # Write data to
    final_data = pd.concat(result, ignore_index=True)
    final_data.to_csv(outputFileName)


if __name__ == "__main__":
    workspace = sys.argv[1]
    outputFileName = sys.argv[2]
    #path = "/Users/chent/Desktop/KOMP_Project/PCP_ERG_data_compilation/data/test1"

    # Collect data from files
    file_groups = organize_files(path=workspace)
    extracted_data = transform(file_groups=file_groups)
    print("Process finished")
