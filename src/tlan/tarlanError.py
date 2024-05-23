#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
            super().__init__("The .tlan file has errors in line " \
                             + str(line_number) + ":", msg)
        else:
            super().__init__("The TARLAN command has errors:", msg)


class TarlanWarning(UserWarning):
    """
    Warning raised when tarlan file has unclear commands.
    """
    def __init__(self, msg: str, line_number: int = 0):
        """
        
        :param msg: Message
        :type msg: str
        :param line_number: Line number in tlam file. Zero for no line / single 
            command 
        :type line_number: int

        """
        if line_number > 0:
            super().__init__("TARLAN parser warning from line" \
                             + str(line_number) + ":", msg)
        else:
            super().__init__("Warning:", msg)

