#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# from collections import OrderedDict
from bisect import insort_left
from typing import Self

if __name__ == '__main__':
    import sys
    sys.path.append("..") # Adds current directory to python modules path.
from src.experiment import Experiment
from src.timeInterval import TimeInterval
from src.const import km, µs, c


class TarlanError(Exception):
    """
    Exception raised when there are errors in parsing a tarlan file
    """
    def __init__(self, msg: str, line_number: int = 0):
        """
        
        :param msg: Error message
        :type msg: str
        :param line_number: Line number in tlam file. Zero for no line / single 
            command 
        :type line_number: int

        """
        if line_number > 0:
            super().__init__("The .tlan file has errors in line", line_number, 
                             ":", msg)
        else:
            super().__init__("The TARLAN command has errors:", msg)



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
        return self.t < other.t
    
    def __repr__(self):
        return f"Command({self.line}: {self.t}, {self.cmd})"
    
class Subcycle:
    """
    Lists commands in single subcycle. Commands are sorted after execution time
    """
    
    def __init__(self, start_subcycle: float = 0) -> None:
        """
        
        :param start_subcycle: start of subcycle in seconds, defaults to 0
        :type start_subcycle: float, optional

        """
        self.start = start_subcycle
        self.commands = []
        
    def add_command(self, cmd: str) -> None:
        """
        Add command to subcycle. 
        :param cmd: command
        :type cmd: str

        """
        insort_left(self.commands, cmd)
        
class DataStreams:
    """
    Contain intervals for when data streams are enabled. 
    Intervals may be open in contrast to TimeInterval, which must contain 
    closed intervals
    """
    
    def __init__(self, name: str):
        """
        
        :param name: Name of datastream
        :type name: str

        """
        self.name = name
        self._streams = []
    
    @property
    def state(self) -> bool:
        """
        
        :raises RuntimeError: if the last stream contains more than one on and 
            off value(should never happen, but who knows...)
        :return: state (on/off) of data stream.
        :rtype: bool

        """
        
        if len(self._streams) == 0:
            on = False
        elif len(self._streams[-1]) == 0:
            on = False
        elif len(self._streams[-1]) == 1:
            on = True
        elif len(self._streams[-1]) == 2:
            on = False
        else:
            raise RuntimeError("There is something bad with the streams:"+
                               str(self._streams))
        return on
    
    @property
    def is_off(self) -> bool:
        """
        If stream is turned off
        
        :type: bool

        """
        return not self.state
    
    @property
    def is_on(self) -> bool:
        """
        If stream is turned on
        
        :type: bool

        """
        return self.state
    
    def turn_on(self, time: float, line: int) -> None:
        """
        Turns on data stream
        
        :param time: time at which to turn on the stream
        :type time: float
        :param line: line in the tlan file. Used for error handling only.
        :type line: int
        :raises TarlanError: if stream is on already

        """
        if self.is_off:
            self._streams.append([time])
        else:
            raise TarlanError(f"Data stream {self.name} is already on!", line)
    
    def turn_off(self, time: float, line: int):
        """
        Turns off data stream
        
        :param time: time at which to turn off the stream
        :type time: float
        :param line: line in the tlan file. Used for error handling only.
        :type line: int
        :raises TarlanError: if stream is off already

        """
        if self.is_on:
            self._streams[-1].append(time)
        else:
            raise TarlanError(f"Data stream {self.name} is already off!", line)
            
    @property
    def nstreams(self) -> int:
        """
        Number of streams
        
        :type: int

        """
        return len(self._streams)
    
    def __len__(self) -> int:
        """
        Number of streams
        
        :type: int

        """
        return self.nstreams
    
    @property
    def intervals(self) -> list[TimeInterval]:
        """
        Return the on-time of the streams as a list of TimeIntervals
        
        :type: list[TimeInterval]

        """
        if self.is_on:
            raise RuntimeError("Stream is on. Cant return open intervals.")
        iv = []
        for i in range(self.nstreams):
            iv.append(TimeInterval(*self._streams[i]))
        return iv

    @property
    def last_turn_off(self) -> float:
        """
        Last time when the stream was turned off
        
        :raises RuntimeError: If there stream has not been turned off yet.
        :type: float

        """
        if self.nstreams == 0:
            raise RuntimeError("Stream has not been turned on yet!")
        elif self.is_off:
            return self._streams[-1][1]
        elif self.nstreams == 1:
            # Is on too
            raise RuntimeError("Stream is on, but has not been turned off yet!")
        else:
            return self._streams[-2][1]
            
            
                
            
            
class Tarlan():
    """
    Class for parsing and handling TARLAN commands
    
    TARLAN commands have function that are written as in the file. When they are run,
        they need argument `time` as a string. This is the time in time control
        and time after start of the file (not the time written in the command)
        that is for SETTCR 0.
    """
    
    def __init__(self, file_name: str = ""):
        """
        Starts reading tlan file
        
        :param file_name: Path of tlan file to load. No file is loaded if 
            string is empty, defaults to ""
        :type file_name: str, optional

        """
        
        streams = ["RF", "CYCLE", "SUBCYCLE"]
        for i in range(1,7):
            streams.append(f"CH{i}")
            
        # Create streams
        self.streams = dict()
        for stream in streams:
            self.streams[stream] = DataStreams(stream)
        
        
        # List of when radio frequency transmitting is toggled
        self._RF = []
        for i in range(1, 7):
            setattr(self, f"_CH{i}", [])
            
        # Time control
        self.TCR = 0
        self.end_time = 0
        
        if file_name:
            self.from_tlan(file_name)
            

    def to_exp(self) -> Experiment:
        """
        Convert loaded tarlan input to Experiment
        
        :raises RuntimeError: If radar controller is not resetted correctly 
            at end of file.
        :raises RuntimeWarning: if transmitter is constantly off.
        :return: object containing experiment information and plotting functions.
        :rtype: Experiment

        """
        exp = Experiment()
        exp.add_stop_time(self.streams["CYCLE"].last_turn_off)
        
        # RF stream
        if self.streams["RF"].is_on:
            raise RuntimeError("RF is not turned off at end of instructions!")
        if len(self.streams["RF"]) > 0:
            for interval in self.streams["RF"].intervals:
                exp.add_transmit_time(interval)
        else:
            raise RuntimeWarning("RF is neither turned on nor off in the instructions!")
        
        # Channel streams
        for i in range(1, 7):
            CH = "CH" + str(i)
            if self.streams[CH].is_on:
                raise RuntimeError(CH + " is not turned off at end of experiment!")
            if len(self.streams[CH]) > 0:
                for interval in self.streams[CH].intervals:
                    exp.add_receive_time(CH, interval)
        
        for interval in self.streams["SUBCYCLE"].intervals:
            exp.add_subcycle(interval)
        
        return exp
    
    
        
    def from_tlan(self, file_name: str = "") -> None:
        """
        Parse tlan file and run Tarlan.eec_cmd() for all commands.
        
        :param file_name: Path of tlan file to load, defaults to ""
        :type file_name: str, optional

        """
        cycle = tarlan_parser(file_name)
        self.streams["CYCLE"].turn_on(0, 0)
        for subcycle in cycle:
            for cmd in subcycle.commands:
                # print(cmd)
                self.exec_cmd(cmd)
    
    def exec_cmd(self, cmd: Command):
        """
        «Execute» TARLAN command / import command to experiment
        
        :param cmd: command as pasrsed from the file.
        :type cmd: Command

        """
        
        if cmd.cmd == "RFON":
            self.streams["RF"].turn_on(self.TCR + cmd.t, cmd.line)
        elif cmd.cmd == "RFOFF":
            self.streams["RF"].turn_off(self.TCR + cmd.t, cmd.line)
        elif cmd.cmd == "REP":
            self.streams["CYCLE"].turn_off(self.TCR + cmd.t, cmd.line)
            self.streams["SUBCYCLE"].turn_off(self.TCR + cmd.t, cmd.line)
        elif cmd.cmd == "CH1":
            self.streams["CH1"].turn_on(self.TCR + cmd.t, cmd.line)
        elif cmd.cmd == "CH1OFF":
            self.streams["CH1"].turn_off(self.TCR + cmd.t, cmd.line)
        elif cmd.cmd == "ALLOFF":
            for i in range(1,7):
                CH = "CH"+str(i)
                if self.streams[CH].is_on:
                    self.streams[CH].turn_off(self.TCR + cmd.t, cmd.line)
        elif cmd.cmd == "SETTCR":
            self.TCR = cmd.t
            if self.streams["SUBCYCLE"].is_on and cmd.t != 0:
                self.streams["SUBCYCLE"].turn_off(cmd.t, cmd.line)
            if self.streams["SUBCYCLE"].is_off:
                self.streams["SUBCYCLE"].turn_on(cmd.t, cmd.line)
        
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
            raise TarlanError("Line starting with 'AT' must include time and command(s)!", line_number)
        
        time = float(args[1])*µs
        
        for arg in args[2:]:
            for cmd in arg.split(","):
                commands.append(Command(time, cmd, line_number))
        
        
    elif args[0] == "SETTCR":
        # Set time control ?
        time = float(args[1])*µs
        
        commands = [Command(time, "SETTCR", line_number)]

    else:
        raise TarlanError("Line must start with 'AT' or 'SRTTCR'. Use '%' for comments.", line_number)
        
    return commands
        
def tarlan_parser(filename: str) -> list[Subcycle]:
    """
    Parse tlan file by running parse_line for every line of code. Commands are
        grouped in Subcycle objects
    
    :param filename: Path to tlan file, defaults to ""
    :type filename: str
    :raises FileNotFoundError: when file is not found / does not exist
    :return: commands grouped in Subcycles.
    :rtype: list[Subcycle]

    """
    
    cycle = []
    
    with open(filename) as file:
        for il, line in enumerate(file):
            cmds = parse_line(line, il+1)
            for cmd in cmds:
                
                print(cmd)
                if cmd.cmd == "SETTCR":
                    try:
                        cycle.append(subcycle)
                    except NameError:
                        pass
                    subcycle = Subcycle(cmd.t)
                subcycle.add_command(cmd)
                if cmd.cmd == "REP":
                    cycle.append(subcycle)
                    break
    return cycle
