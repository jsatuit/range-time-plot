#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
    
    def parse_args(self, args: list[str]) -> None:
        """
        Parses TARLAN arguments by running the function in the Tarlan class with the same name.
        
        There must be at least two arguments. The first is the time the command is executed, the second atre 
        
        :param args: list of arguments
        :type args: list[str]
        :raises TarlanError: If there are too few arguments
        :rtype: None

        """
        
        # Argument must contain at least time and commands
        if len(args) < 2:
            raise TarlanError("The line must contain of 'AT', timepoint and command(s), in that order!", self.reading_line)
        
                                   
        time = args[0]
        cmds = []
        for arg in args:
            for cmd in arg.split(","):
                cmds.append(cmd)
        
        for cmd in cmds:
            # «Run» the commands
            if hasattr(self,cmd):
                f = getattr(self, cmd)
                f(time)
        
    def parse_line(self, line: str):
        # Filter away comments
        codeline = line.split("%")[0]
        
        # Unpack arguments
        args = codeline.split()
        
        if len(args) == 0:
            pass
        elif args[0] == "AT":
            # The radar hardware is doing something!
            self.parse_args(args[1:])
            
        elif args[0] == "SETTCR":
            # Set time control ?
            if float(args[1]) > 0:
                # Jump over the rest, now we need only one pulse
                raise StopIteration
        else:
            raise TarlanError("Line must start with 'AT' or 'SRTTCR'. Use '%' for comments.", self.reading_line)
            
    def tarlan_parser(self, filename: str = ""):
        
        with open(filename) as file:
            for il, line in enumerate(file):
                self.reading_line = il + 1

                try:
                    self.parse_line(line)
                except StopIteration:
                    break

            self.reading_line = 0
