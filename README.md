# range-time-plotter of TARLAN files

Python package for showing a range-time-plot for an EISCAT KST experiment. 

## Notes
- In most cases, the program should divides experiment cyclus correctly into subcycles. In some cases, the program may divide into subcycles in a wrong way because of assumptions on time structure of the .tlan file. This program presumes that experiment cycle is divided into subcycles by the command SETTCR as long as the following number is not zero. Using SETTCR to divide experiment into subcycles is not nessesary or obligatory. Therefore, there may be experiments that are shown with strange subcycle divison.


# Running
python3 -m src <path-to-.tlan-file>

## Dependencies
- Python 3.11 or newer
- numpy 
- matplotlib

Tests are run with pytest
