# EISCAT KST experiment plotter

Python package for showing a range-time-plot for an EISCAT KST experiment. 

## Notes
- In most cases, the program should divides experiment cyclus correctly into subcycles. In some cases, the program may divide into subcycles in a wrong way because of assumptions on time structure of the .tlan file. This program presumes that experiment cycle is divided into subcycles by the command SETTCR as long as the following number is not zero. Using SETTCR to divide experiment into subcycles is not nessesary or obligatory. Therefore, there may be experiments that are shown with strange subcycle divison.


# Install and run
Download program and dependencies
```git clone git@github.com:jsatuit/range-time-plot.git
cd range-time-plot
python3.11 -m venv env-rtp
source env-rtp/bin/avtivate
pip install -r requirements.txt
```
Start program plotting
`python -m src <path-to-experiment> (<subcycle number>)`

- The experiment may be given as a .elan or -.tlan file.
- Subcycle number 0 plots all subcycles (default)

## Example
- `python -m src beata/beata.elan 0`
- `python -m src beata/beata 1`
- `python -m src kst/exp/beata/beata-u.tlan 2`
