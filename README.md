# EISCAT KST experiment plotter

Python package for showing a range-time-plot for EISCAT mainland (KST) experiments and some properties of the experiment.

The program should be able to plot all standard experiments

## Notes
- Documentation of EISCAT experiments can be found on the [EISCAT website](https://eiscat.se/scientist/schedule/experiments/)
- **Experiment files are not included** in this repository. To be able to run this program, you must have some. 
- In most cases, the program should divides experiment cycle correctly into subcycles. In some cases, the program may divide into subcycles in a wrong way because of assumptions on time structure of the .tlan file. This program presumes that experiment cycle is divided into subcycles by the command SETTCR as long as the following number is not zero. Using SETTCR to divide experiment into subcycles is not nessesary or obligatory. Therefore, there may be experiments that are shown with strange subcycle divison.
- Some plots of the discontinued experiment `cp1l` are empty. This is correct behaviour. The experiment starts with an empty subcycle and every fourth subcycle is without transmission or reception. 


# Install and run
Download program and install dependencies in a virtual environment
```git clone git@github.com:jsatuit/range-time-plot.git
cd range-time-plot
python3.11 -m venv env-rtp
source env-rtp/bin/activate
pip install -r requirements.txt
```
Start program plotting
`python -m src <path-to-experiment> (<subcycle number>)`

- The experiment may be given as a .elan or .tlan file. If the .tlan file is given, frequencies are not plotted or not plotted correctly because frequency shifting is not controlled by radar controller, but Eros.
- Subcycle number 0 plots all subcycles (default)

The plot will show as a matplotlib window.

## Examples

- `python -m src beata/beata.elan 0`
- `python -m src beata/beata 1`
- `python -m src kst/exp/beata/beata-u.tlan 2`
