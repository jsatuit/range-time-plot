# User guide
This page describes how to use the experiment plotter. The program is controlled by command-line only and this guide assumes a linux shell.

## Installation
Download program and install dependencies in a virtual environment
:::{code-block}
git clone git@github.com:jsatuit/range-time-plot.git
cd range-time-plot
:::
Create and activate virtual environment
:::{code-block}
python3.11 -m venv env-rtp
source env-rtp/bin/activate
:::
Install dependencies
`pip install -r requirements.txt`

## Get experiment files
The experiment files must be accessible to experiment plotter by being in one of the directories:
- experiment directory as subfolder of this program: `range-time-plot/kst/exp/*` (recommended)
- as a direct subfolder of this program: `range-time-plot/beata`for `beata` experiment.
- `/kst/exp/*`, that is mounted at root of the system

The program will look into all of these directories for the experiment files.

If none of these are applicable, but you still have experiment files available on your computer, you can create a symbolic link to the experiment folder. 


## Plot `beata` experiment
This requires that you have the experiment files for the beata experiment in an directory as described above.

To activate virtual environment, run
:::{code-block}
source env-rtp/bin/activate
:::
To plot first subcycle of beata experiment, run 
:::{code-block}
python -m src beata/beata 1
:::
The program will now look for the file `beata/beata.elan` in current directory, else `kst/exp/beata/beata.elan` or `/kst/exp/beata/beata.elan`. Then it parses the file, looking for other files to load, radar controller source file `beata-u.tlan` and files for frequency shifting (.nco files) and parses those as well.
This may take a second or two. 

When finished parsing, the program opens a matplotlib window showing the first subcycle og the beata experiment.
