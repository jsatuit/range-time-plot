#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class TarlanError(Exception):
    """
    Exception raised when there are errors in parsing a tarlan file
    """
    def __init__(self, line, msg):
        super().__init__("The .tlan file has errors in line", line, ":", msg)


class Tarlan():
    tarlan_commands = {
        "CHQPULS": "High output on bit 31 for 2 us, used for synchronization with external hardware.",
        "RXPROT": "Enable receiver protector, bit 12 high",
        "LOPROT": "Enable local oscillator protector, bit 6 high",
        "BEAMON": "Enable beam in klystron, bit 13 high",
        "RFON": "Enable RF output, bit 11 high",
        "RFOFF": "Disable RF output, bit 11 low"
        }  #  etc.
    
    def __init__(self, file_name: str):
    
        # Times (microseconds) where RF is turned on or off
        self.RF = []
        
        # Times where channels are tunred on or off
        self.CHS = {}
        
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
            raise TarlanError(self.reading_line, "RF output is already on / Transmitter is transmitting already!")
            
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
            raise TarlanError(self.reading_line, "RF output is off!")
    
    def parse_params(self, params: list[str]) -> None:
        N = len(params) 
        if N < 2:
            raise RuntimeError("The line must contain of 'AT', timepoint and command(s), in that order!")
        
                                   
        time = params[0]
        
        cmds = params[1].split(",")
        for cmd in cmds:
            # pass
            # if cmd in tarlan_commands.keys():
                # print(tarlan_commands[cmd].split(",")[0], "at", time, "µs")
            if hasattr(self,cmd):
                f = getattr(self, cmd)
                f(time)
        
    
    def tarlan_parser(self, filename: str = ""):
        
        with open(filename) as file:
            for il, line in enumerate(file):
                self.reading_line = il
                # Filter away comments
                codeline = line.split("%")[0]
                
                
                strs = codeline.split()
                
                # If empty line
                if len(strs) == 0:
                    continue
                
                if strs[0] == "AT":
                    # The radar hardware is doing something!
                    params = strs[1:]
                    
                    self.parse_params(params)
                    
                elif strs[0] == "SETTCR":
                    # Set time control ?
                    if float(strs[1]) > 0:
                        # Jump over the rest, now we need only one pulse
                        break
                    
                else:
                    raise RuntimeError("Was not able to parse tarlan line! {line}")
            delattr(self, "reading_line")
