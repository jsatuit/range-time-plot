#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# from collections import OrderedDict


class TarlanError(Exception):
    """
    Exception raised when there are errors in parsing a tarlan file
    """
    def __init__(self, msg: str, line_number: int = 0):
        if line_number > 0:
            super().__init__("The .tlan file has errors in line", line_number, ":", msg)
        else:
            super().__init__("The TARLAN command has errors:", msg)




class Tarlan():
    tarlan_commands = {
        "CHQPULS": "High output on bit 31 for 2 us, used for synchronization with external hardware.",
        "RXPROT": "Enable receiver protector, bit 12 high",
        "LOPROT": "Enable local oscillator protector, bit 6 high",
        "BEAMON": "Enable beam in klystron, bit 13 high",
        "RFON": "Enable RF output, bit 11 high",
        "RFOFF": "Disable RF output, bit 11 low"
        }  #  etc.
    
    def __init__(self, file_name: str = ""):
    
        # Times (microseconds) where RF is turned on or off
        self.RF = []
        
        # Times where channels are tunred on or off
        self.CHS = {}
        
        # We are not reading a file right now
        self.reading_line = 0
        
        if len(file_name) > 0:
            self.tarlan_parser(file_name)
        
    def RFON(self, time: str):
        """
        Enable RF output, bit 11 high
        
        :param time: Time in time control
        :type time: str
        :raises TarlanError: If transmitter is on

        """
        print("Enable RF output")
        # If is even
        if len(self.RF)%2 == 0:
            t = float(time)
            self.RF.append(t)
        else:
            raise TarlanError("RF output is already on / Transmitter is transmitting already!", self.reading_line)
            
    def RFOFF(self, time: str):
        """
        Disable RF output, bit 11 low
        
        :param time: Time in time control
        :type time: str
        :raises TarlanError: If transmitter is off

        """
        print("Disable RF output")
        # If is even
        if len(self.RF)%2 == 1:
            t = float(time)
            self.RF.append(t)
        else:
            raise TarlanError("RF output is off!", self.reading_line)
    
    
def parse_line(line: str, line_number: int = 0) -> tuple[float, list[str]]:
    """
    Parse single line of Tarlan code.
    
    :param line: line of code
    :type line: str
    :param line_number: line number in file, used for error handling only, defaults to 0
    :type line_number: int, optional
    :raises TarlanError: for invalid commands
    :return: time and list of commands
    :rtype: tuple[float, list[str]]

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
        
        time = float(args[1])
        
        for arg in args[2:]:
            for cmd in arg.split(","):
                commands.append(cmd)
        
        
    elif args[0] == "SETTCR":
        # Set time control ?
        time = float(args[1])
        
        commands = ["SETTCR"]

    else:
        raise TarlanError("Line must start with 'AT' or 'SRTTCR'. Use '%' for comments.", line_number)
        
    return time, commands
        
def tarlan_parser(filename: str = "") -> dict[float,dict[float,list[str]]]:
    
    cycle_commands = {}
    
    subcycle_start_time = 0.0
    
    with open(filename) as file:
        for il, line in enumerate(file):
            t, cmds = parse_line(line, il+1)
            if cmds:
                if "SETTCR" in cmds:
                    subcycle_start_time = t
                    if subcycle_start_time not in cycle_commands.keys():
                        cycle_commands[subcycle_start_time] = {}
                else:
                    cur_subcycle = cycle_commands[subcycle_start_time]
                    cur_subcycle[t] = cmds
                    if "REP" in cmds:
                        break
    return cycle_commands
