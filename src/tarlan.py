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
        if line_number > 0:
            super().__init__("The .tlan file has errors in line", line_number, ":", msg)
        else:
            super().__init__("The TARLAN command has errors:", msg)



class Command:
    """
    Tarlan command.
    
    :param float t: Subcycle time when command is executed.
    :param str cmd: Command as written in the .tlan file
    
    """
    
    def __init__(self, time: float, cmd: str):
        """
        
        :param time: Subcycle time when command is executed.
        :type time: float
        :param cmd: Command as written in the .tlan file
        :type cmd: str

        """
        self.t = time
        self.cmd = cmd
        
    def __lt__(self, other: Self) -> bool:
        return self.t < other.t
    
    def __repr__(self):
        return f"Command({self.t}, {self.cmd})"
    
class Subcycle:
    """
    Not used at the moment
    """
    
    def __init__(self, start_subcycle: float = 0):
        self.start = start_subcycle
        self.commands = []
        
    def add_command(self, cmd: str) -> None:
        insort_left(self.commands, cmd)
        
class DataStreams:
    def __init__(self, name: str):
        self.name = name
        self._streams = []
        self._on = []
        self._off = []
    
    @property
    def state(self):
        
        # if len(self._on) == len(self._off):
        #     on = False
        # elif len(self._on) == len(self._off) + 1:
        #     on = True
        # else:
        #     raise RuntimeError(f"Data stream {self.name} is turned on {len(self.on)} times and off {len(self.off)} times. This is not allowed!")
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
        return not self.state
    
    @property
    def is_on(self) -> bool:
        return self.state
    
    def turn_on(self, time: float, line: int):
        if self.is_off:
            self._streams.append([time])
        # if len(self._on) == len(self._off):
        #     self._on.append(time)
        else:
            raise TarlanError(f"Data stream {self.name} is already on!", line)
    
    def turn_off(self, time: float, line: int):
        if self.is_on:
            self._streams[-1].append(time)
        # if len(self._on) - 1 == len(self._off):
        #     self._off.append(time)
        else:
            raise TarlanError(f"Data stream {self.name} is already off!", line)
            
    @property
    def nstreams(self) -> int:
        # return len(self._on)
        return len(self._streams)
    
    def __len__(self) -> int:
        # return len(self._on)
        return self.nstreams
    
    @property
    def intervals(self) -> list[TimeInterval]:
        if self.is_on:
            raise RuntimeError("Stream is on. Cant return open intervals.")
        iv = []
        for i in range(self.nstreams):
            # iv.append(TimeInterval(self._on[i], self._off[i]))
            iv.append(TimeInterval(*self._streams[i]))
        return iv

    @property
    def last_turn_off(self):
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
            
            #Time control
        self.TCR = 0
        self.end_time = 0
        
        if file_name:
            self.from_tlan(file_name)
            

    def to_exp(self) -> Experiment:
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
    
    
        
    def from_tlan(self, file_name: str = ""):
        cycle = tarlan_parser(file_name)
        self.streams["CYCLE"].turn_on(0, 0)
        for subcycle in cycle:
            for cmd in subcycle.commands:
                # print(cmd)
                self.exec_cmd(cmd, 0)
    
    def exec_cmd(self, cmd: Command, line: int):
        
        if cmd.cmd == "RFON":
            self.streams["RF"].turn_on(self.TCR + cmd.t, line)
        elif cmd.cmd == "RFOFF":
            self.streams["RF"].turn_off(self.TCR + cmd.t, line)
        elif cmd.cmd == "REP":
            self.streams["CYCLE"].turn_off(self.TCR + cmd.t, line)
            self.streams["SUBCYCLE"].turn_off(self.TCR + cmd.t, line)
        elif cmd.cmd == "CH1":
            self.streams["CH1"].turn_on(self.TCR + cmd.t, line)
        elif cmd.cmd == "CH1OFF":
            self.streams["CH1"].turn_off(self.TCR + cmd.t, line)
        elif cmd.cmd == "ALLOFF":
            for i in range(1,7):
                CH = "CH"+str(i)
                if self.streams[CH].is_on:
                    self.streams[CH].turn_off(self.TCR + cmd.t, line)
        elif cmd.cmd == "SETTCR":
            self.TCR = cmd.t
            if self.streams["SUBCYCLE"].is_on and cmd.t != 0:
                self.streams["SUBCYCLE"].turn_off(cmd.t, line)
            if self.streams["SUBCYCLE"].is_off:
                self.streams["SUBCYCLE"].turn_on(cmd.t, line)
        
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
                commands.append(Command(time, cmd))
        
        
    elif args[0] == "SETTCR":
        # Set time control ?
        time = float(args[1])*µs
        
        commands = [Command(time, "SETTCR")]

    else:
        raise TarlanError("Line must start with 'AT' or 'SRTTCR'. Use '%' for comments.", line_number)
        
    return commands
        
def tarlan_parser(filename: str = "") -> list[Subcycle]:
    
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
