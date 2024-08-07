#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# from collections import OrderedDict
"""
The Transmit And Receiver LANguage (TARLAN) is the language for the radar controllers
at the EISCAT mainland radars, that are EISCAT UHF and VHF, including receivers
in Kiruna and Sodankylä.

The radar controller controls most of the physical radar equipment, that is 
phase shifting, beams, transmittion, reception, but not antenna steering or 
signal processing.

The dictionary `Tarlan.commands` gives an overview over the commands the system
can run. More infortmation can be found at
https://eiscat.se/scientist/user-documentation/radar-controllers-and-programming-for-the-kst-system/
"""
import functools
import numpy as np

from warnings import warn
from typing import Self

from src.phaseshifter import PhaseShifter
from src.frequencyshift import FrequencyList
from src.kstconfig.nco import Nco
from src.tlan.tarlanIntervals import IntervalList, TarlanSubcycle
from src.tlan.tarlanError import TarlanError, TarlanWarning
from src.eventlist import EventList
from src.const import km, µs, c

tarlan_command_docstring =\
    """:param time: time [s]
:type time: float
:param line: line where the command is found. Used for error handling only.
:type line: int"""
"""Docstring ito be inserted to all tarlan commands."""


def kst_channels():
    "List of available channels"

    chs = []
    for i in range(1, 7):
        chs.append(f"CH{i}")
    return chs


def do_nothing(*args):
    """Dont delete. This function is needed for executing tarlan commands that 
       cant be simulated/transferred or where is would not make sense to 
       implement the function here."""
    pass


class Command:
    """
    Tarlan command.

    :param float t: Subcycle time in seconds when command is executed.
    :param str cmd: Command as written in the .tlan file
    :param int line: Line in tlan file. Used for error messages

    """

    def __init__(self, t: float, cmd: str, line: int = 0):
        """

        :param t: Subcycle time in seconds when command is executed.
        :type t: float
        :param cmd: Command as written in the .tlan file
        :type cmd: str
        :param line: Line in tlan file. Used for error messages, defaults to 0.
        :type line: int

        """
        self.t = t
        self.cmd = cmd
        self.line = line

    def __lt__(self, other: Self) -> bool:
        # Is used for sorting. Therefore only the time matters
        return self.t < other.t

    def __repr__(self):
        return f'Command({self.t}, "{self.cmd}", {self.line})'

    def __str__(self):
        return f"{self.line}: {self.t/µs} {self.cmd}"


class Tarlan():
    """
    Class for parsing and handling an TARLAN experiment

    :param IntervalList cycle: Begin and end of experiment cycle
    :param IntervalList subycle: Begin and end of experiment subcycles. These
        are defined by when SETTCR <time> is called.
    :param dict[str, IntervalList] streams: Dictionary of all on/off times of 
        the different settings in the radar system controller, among others
        "RF", "CH1".
    :param float end_time: Length of tarlan program in seconds.
    """

    command_docs = {
        "CHQPULS": "High output on bit 31 for 2 us, used for synchronization " +
        "with external hardware.",
        "RXPROT": "Enable receiver protector, bit 12 high",
        "RXPOFF": "Disable receiver protector, bit 12 low",
        "LOPROT": "Enable local oscillator protector, bit 6 high",
        "LOPOFF": "Disable local oscillator protector, bit 6 low",
        "BEAMON": "Enable beam in klystron, bit 13 high",
        "BEAMOFF": "Disable beam in klystron, bit 13 low",
        "RFON": "Enable RF output, bit 11 high",
        "RFOFF": "Disable RF output, bit 11 low",
        "PHA0": "Set proper phase, bit 4 low",
        "PHA180": "Set proper phase, bit 4 high",
        "CALON": "Tromsø and receivers: Enable noise source for calibration, bit 15 high.",
        "CAL100": "Enable noise source for calibration, bit 15 high.",
        "CALOFF": "Tromsø and receivers: Disable noise source, bit 15 low.",
        "CAL0": "Disable noise source for calibration, bit 15 low.",
        "HCALON": "Remote receivers: enable noise source in only horisontal " +
        "wave guide, high bit 1 high",
        "HCALOFF": "Remote receivers: disable noise source in only horisontal " +
        "wave guide, high bit 1 low",
        "VCALON": "Remote receivers: enable noise source in only vertical " +
        "wave guide, high bit 1 high",
        "VCALOFF": "Remote receivers: disable noise source in only vertical " +
        "wave guide, high bit 1 low",
        "STC": "Send a interrupt to crate computer to signal that new data are " +
        "available a needs to be taken care of, bit 8 high strobed.",
        "BUFLIP": "Change side of buffer memory in channel boards, bit 17 high strobed.",
        "ALLOFF": "Close sampling gate on all channel boards, bit 10-15 low",
        "REP": "End of tarlan program/repeat cycle",
        "SETTCR": "Set reference time in time control?",
        "RXSYNC": "A 2 us pulse on bit 31 on the front of the receiver controller.",
        "TXSYNC": "A 2 us pulse on bit 31 on the front of the transmitter controller.",
        "AD1L": "Route input from AD 1 to channel board 1, 2, 3.",
        "AD1R": "Route input from AD 1 to channel board 4, 5, 6.",
        "AD2L": "Route input from AD 2 to channel board 1, 2, 3.",
        "AD2R": "Route input from AD 2 to channel board 4, 5, 6.",
        "STFIR": "Start the fir filters onboard channel boards, necessary " +
        "to do before using them, bit 16 strobed.",
        "TRANS": "Not documented.",
        "RECEV": "Not documented.",
    }
    for i in range(16):
        command_docs["F" + str(i)] = "Set transmitter frequency, bit 0-3 high"
    for i in range(1024):
        command_docs["NCOSEL" + str(i)] = "Load the frequency defined in the " +\
            "requested memory into the NCO plus strobe bit 29."
    for ch in kst_channels():
        command_docs[ch] = \
            f"Open sampling gate on the referenced channel board, bit {i+9} high"
        command_docs[ch + "OFF"] = \
            f"Close sampling gate on the referenced channel board, bit {i+9} low"
    for i in range(32):
        command_docs["BRX" + str(i)] = f"Set bit {i} on receiver controller. " +\
            "No checks are made."
        command_docs["BRX" + str(i) + "OFF"] = f"Set bit {i} on receiver controller. " +\
            "No checks are made. "
        command_docs["BTX" + str(i)] = f"Set bit {i} on transmitter controller. " +\
            "No checks are made. Use with caution."
        command_docs["BTX" + str(i) + "OFF"] = f"Set bit {i} on transmitter controller. " +\
            "No checks are made. Use with caution."

    def __init__(self, filename: str = "", lo1: tuple[float, float] = (812e6,)*2,
                 lo2: tuple[float, float] = (128e6, 122e6), chfreqs: dict[int, Nco] | None = None):
        """
        Initializing Tarlan(). If .tlan file is specified, it will be loaded.

        :param str, optional filename: Path of tlan file to load. No file is loaded if 
            string is empty, defaults to ""
        :param tuple[float, float], optional lo1: Frequencies in first local oscillator [Hz]. One frequency for each path, two in total. UHF lo1 must be inserted twice.
        :param tuple[float, float], optional lo2: Frequencies in second local oscillator [Hz]. One frequency for each path, two in total
        :param dict[int, Nco] | None chfreqs: Dictionary of channel numbers with correspondig Nco objects. 
            These are used to store the current frequency of data in this channel. If None, all 6 channels are loaded with NCO only 8.5 MHz. Defaults to None

        """
        self.cycle = IntervalList("CYCLE")
        # self.subcycle_list = IntervalList("SUBCYCLE")
        self.subcycle_list = TarlanSubcycle()
        self.phaseshifter = PhaseShifter()
        self.freq_rec = {}
        for ch in range(1, 7):
            self.freq_rec[ch] = FrequencyList()

        self.stream_names = ["RF", "RXPROT", "LOPROT", "CAL", "BEAM"]
        for ch in kst_channels():
            self.stream_names.append(ch)
        self._init_streams()
        self._generate_commands()
        self._check_command_docs()
        self._loaded_FIR = False
        self._selected_ADL = False
        self._selected_ADR = False
        self._selected_NCO = False

        # Time control
        self.TCR = 0
        self.end_time = 0

        self._lo1 = lo1
        self._lo2 = lo2
        if chfreqs is None:
            self.chfreqs = {}
            for ch in range(1, 7):  # From 1 to 6
                self.chfreqs[ch] = Nco(lo1=lo1[1]/1e6, lo2=lo2[1]/1e6)
        else:
            self.chfreqs = chfreqs

        if filename:
            self.from_tlan(filename)

    def _init_streams(self):
        # Create streams
        self.streams = dict()
        for stream in self.stream_names:
            self.streams[stream] = IntervalList(stream)

    def from_tlan(self, filename: str = "") -> None:
        """
        Parse tlan file and run Tarlan.exec_cmd() for all commands.

        :param filename: Path of tlan file to load, defaults to ""
        :type filename: str, optional

        """
        cmd_list = tarlan_parser(filename)

        for cmd in cmd_list:

            # First subcycle
            if self.cycle.is_off:
                self.cycle.turn_on(0, cmd.line)
                self.subcycle_list.turn_on(0, cmd.line)

            """ Use SETTCR as start and stop of subcycles.
            In this implementation, SETTCR 0 means that subcycle is continued."""
            if cmd.cmd == "SETTCR":

                if cmd.t > 0:
                    self.subcycle_list.turn_off(cmd.t, cmd.line, self.streams)

                    # Delete connection to last subcycle streams
                    self._init_streams()

                    self.subcycle_list.turn_on(cmd.t, cmd.line)
                self.SETTCR(cmd.t, cmd.line)

            elif cmd.cmd == "REP":
                # self.PHA_OFF(cmd.t, cmd.line)
                self.subcycle_list.turn_off(cmd.t, cmd.line, self.streams)
                # Delete connection to last subcycle streams
                self._init_streams()
                self.cycle.turn_off(cmd.t, cmd.line)
            else:
                self.exec_cmd(cmd)
        self.filename = filename

    def _AD2CH(self, time: float, line: int, path: int, channels: list[int]):
        f"""
        Routes selected receiver path (1 or 2) into selected channels

        {tarlan_command_docstring}
        :param route: selected receiver path (1 or 2)
        :type route: int
        :param channels: Channels the receiver path will be routed into. May be chosen freely as this is not a real TARLAN command, but a helper.
            If the channel is not loaded into tarlan, it is ignored.
        :type channels: list[int]

        """
        for ch, nco in self.chfreqs.items():
            if ch in channels:
                if path == 1 and len(self._lo1) == 1:
                    # If at UHF and path 2 is chosen, still lo1 is used. The split is after lo1.
                    lo1 = self._lo1[0]/1e6
                else:
                    lo1 = self._lo1[path]/1e6
                    
                nco.set_lo1(lo1)
                nco.set_lo2(self._lo2[path]/1e6)
                if nco.is_ready:
                    self.freq_rec[ch][time] = nco.get_freq()*1e6
                    # print(f"Channel {ch} now has center frequency {nco.get_freq()} MHz")

    def AD1L(self, time: float, line: int):
        self._AD2CH(time, line, 0, [1, 2, 3])
        self._selected_ADL = True

    def AD1R(self, time: float, line: int):
        self._AD2CH(time, line, 0, [4, 5, 6])
        self._selected_ADR = True

    def AD2L(self, time: float, line: int):
        self._AD2CH(time, line, 1, [1, 2, 3])
        self._selected_ADL = True

    def AD2R(self, time: float, line: int):
        self._AD2CH(time, line, 1, [4, 5, 6])
        self._selected_ADR = True

    def ALLOFF(self, time: float, line: int):
        f"""
        Turn off signal reception with all channels

        {tarlan_command_docstring}

        """
        for i in range(1, 7):
            CH = "CH"+str(i)
            if self.streams[CH].is_on:
                self.streams[CH].turn_off(time, line)

    def NCOSEL(self, time: float, line: int, nco_line: int):
        for ch, nco in self.chfreqs.items():
            print(ch, nco)
            nco.NCOSEL(nco_line)
            # Log change
            self.freq_rec[ch][time] = nco.get_freq()*1e6
            # print(f"NCOSEL: Channel {ch} now has center frequency {nco.get_freq()} MHz")
        self._selected_NCO = True

    def STFIR(self, time: float, line: int):
        if self._loaded_FIR > 0:
            # warn(f"STFIR was called on line {line}, but FIR filters are " +
            # "loaded already!", TarlanWarning)
            pass
        else:
            self._loaded_FIR = time

    def SETTCR(self, time: float, line: int):
        "Set reference time in time control"
        self.TCR = time

    def _generate_commands(self):
        # """Implement other TARLAN commands.
        #
        # These are:
        #
        # """

        #### Implement TARLAN commands from here ####
        commands = {
            "TRANS": do_nothing,  # No documentation
            "RECEV": do_nothing,  # No documentation
            "RFON": self.streams["RF"].turn_on,
            "RFOFF": self.streams["RF"].turn_off,
            "RXPROT": self.streams["RXPROT"].turn_on,
            "RXPOFF": self.streams["RXPROT"].turn_off,
            "LOPROT": self.streams["LOPROT"].turn_on,
            "LOPOFF": self.streams["LOPROT"].turn_off,
            "CALON": self.streams["CAL"].turn_on,
            "CAL100": self.streams["CAL"].turn_on,
            "CALOFF": self.streams["CAL"].turn_off,
            "CAL0": self.streams["CAL"].turn_off,
            "BEAMON": self.streams["BEAM"].turn_on,
            "BEAMOFF": self.streams["BEAM"].turn_off,
            "PHA0": self.phaseshifter.PHA0,
            "PHA180": self.phaseshifter.PHA180,
            "ALLOFF": self.ALLOFF,
            "STFIR": self.STFIR,
            "RXSYNC": do_nothing,  # Synchronization not implemented
            "CHQPULS": do_nothing,  # Synchronization not implemented
            "TXSYNC": do_nothing,  # Synchronization not implemented
            "AD1L": self.AD1L,
            "AD1R": self.AD1R,
            "AD2L": self.AD2L,
            "AD2R": self.AD2R,
            "SETTCR": do_nothing,  # Is not handeled here!
            "BUFLIP": do_nothing,  # Too technical here
            "STC": do_nothing,  # Too technical here
        }
        # Add receiver channel commands
        for ch in kst_channels():
            commands[ch] = self.streams[ch].turn_on
            commands[ch+"OFF"] = self.streams[ch].turn_off

        # Handling Frequencies is not yet implemented
        # TODO: handle frequencies
        for f in range(16):
            freq = f"F{f}"
            commands[freq] = do_nothing
        # TODO handle frequencies...
        for fline in range(1024):
            sl = f"NCOSEL{fline}"
            commands[sl] = functools.partial(self.NCOSEL, nco_line=fline)

        ''' 
        Silent warnings on setting single bits 4 or 5 in transmit and receive 
        controllers. These go to ADC samplegate, but are not of interest here.
        '''
        for i in [4, 5]:
            for d in ["R", "T"]:
                commands[f"B{d}X{i}"] = do_nothing
                commands[f"B{d}X{i}OFF"] = do_nothing
        #### Implement TARLAN commands to here ####
        self.commands = commands

    def _check_command_docs(self):
        # Check that all commands have docstring
        for cmd in self.commands.keys():
            if cmd not in self.command_docs.keys():
                print("Command", cmd, "has no docstring!")

    def exec_cmd(self, cmd: Command):
        """
        «Execute» TARLAN command / import command to experiment

        :param cmd: command as pasrsed from the file.
        :type cmd: Command

        """
        if self.cycle.is_off:
            raise TarlanError("The cycle has not been started!", cmd.line)

        if self.subcycle_list.is_off:
            raise TarlanError("No subcycle has been started yet!", cmd.line)

        # Has to be done again and again because python does some strange
        # function saving?
        self._generate_commands()

        if cmd.cmd in self.commands.keys():
            # print(self.TCR, cmd.t)
            self.commands[cmd.cmd](self.TCR + cmd.t, cmd.line)
        else:
            warn(f"Command {cmd.cmd}, called from line {cmd.line} " +
                 "is not implemented yet", TarlanWarning)

    def phaseshifts(self, idx: int = 0) -> tuple[EventList, list[float]]:

        # Does this subcycle exist (or has it been parsed yet?)

        sc_interval = self.subcycle_list.intervals[idx]
        tx_intervals = self.subcycle_list.data_intervals[idx]["RF"].intervals

        return self.phaseshifter.phase_shifts_within(sc_interval, tx_intervals)


def parse_line(line: str, line_number: int = 0) -> list[Command]:
    """
    Parse single line of Tarlan code.

    :param line: line of code
    :type line: str
    :param line_number: line number in file, used for error handling only, defaults to 0
    :type line_number: int, optional
    :raises TarlanError: for invalid commands
    :return: list of Command objects
    :rtype: list[Command]

    """
    time = 0
    commands = []

    # Filter away comments
    codeline = line.split("%")[0]

    # Unpack arguments
    args = codeline.split()

    if len(args) == 0:
        pass
    elif args[0] == "AT":
        # The radar hardware is doing something!
        if len(args) < 3:
            raise TarlanError(
                "Line starting with 'AT' must include time and command(s)!", line_number)

        time = float(args[1])*µs

        for arg in args[2:]:
            for cmd in arg.split(","):
                commands.append(Command(time, cmd, line_number))

    elif args[0] == "SETTCR":
        # Set time control ?
        time = float(args[1])*µs

        commands = [Command(time, "SETTCR", line_number)]

    else:
        raise TarlanError(
            "Line must start with 'AT' or 'SETTCR'. Use '%' for comments.", line_number)

    return commands


def tarlan_parser(filename: str = "") -> list[Command]:
    """
    Parse tlan file. Commands are returned in the same order as they appear in 
    the file.

    :param filename: filename, defaults to ""
    :type filename: str
    :return: list of Command objects
    :rtype: list[Command]

    """
    cmd_list = []
    with open(filename) as file:
        for il, line in enumerate(file):
            cmds = parse_line(line, il+1)
            for cmd in cmds:
                cmd_list.append(cmd)
                if cmd.cmd == "REP":
                    break
    return cmd_list
