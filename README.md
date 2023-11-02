## Overview

This repository is intending to help PCP teams collect data from raw files.
The script takes two input from command line:
1. Path to your workspace/folder
2. Output filename

It will read and parse the files in the folder you input to collect data and organize 
them into a `.csv` file. Be sure to include `.csv` when input your output filename. 

<br>

## Installation

Assume that you alhready have the python install, first, create a virtual environment for running the application, I use `venv`, you can pick whatever suites you. 

```
python -m venv .env/ENV_NAME
```
After creating the enviroment, activate it use the following coomand 

```
. . env/ENV_NAME/bin/activate
```

Then use the following command to clone the repository to the `venv` you just created:

```
 git clone https://github.com/TheJacksonLaboratory/PCP_Data_Collect.git

```

Install the reuired packages:

```
pip install requirements.txt
```
<br>

## Usage
In order to use the app, run the following command:
```commandline
python PCP_Transform.py -d path/to/your/dir/ -f filename.csv
```
, where `-d` refers to the directory you want to work with and `-f` is the desired filename of yours. 