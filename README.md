# range-time-plotter of TARLAN files

Python package for showing a range-time-plot for an EISCAT (KST or ESR) experiment. 

## Notes
- The program may divide into subcycles in a wrong way because of assumptions on time structure of the .tlan file. This program presumes that experiment cycle is divided into subcycles by the command SETTCR as long as the following number is not zero. Using SETTCR to divide experiment into subcycles is not nessesairy or obligatory. Thertefore, there may be experiments that are shown with strange subcycle divison


# Running
python3 -m src <path-to-.tlan-file>

## Dependencies
- Python 3.11 or newer
- numpy 
- matplotlib
- click

Tests are run with pytest
