"""
Handling .nco files.

At EISCAT, these are loaded by the numerical controlled oscillator. These shift frequency of the signal 
that comes into a channel. When reading these files, one should be aware of that when the signal comes into the channels, its frequency already is shifted twice.

See also [Jussis EISCAT portal]
(https://portal.eiscat.se/jussi/eiscat/erosdoc/uhf_radar.html)
"""
import os

class Nco:
    """Parsing and handling of numerically controlled oscillator (NCO) files.
    """

    def __init__(self, filename: str, lo1: float = 812, lo2: float = 128) -> None:
        """
        Initialise numerically controlled oscillator for single channel

        :param str filename: Path to .nco file or content of .nco file
        :param float lo1: Local oscillator 1 frequency [MHz]. Default is 812 MHz
        :param float lo2: Local oscillator 2 frequency [MHz]. Default is 128 MHz
        :raises ValueError: If file not has valid data.
        
        Frequencies are for that branch that leads to this channel.

        """
        if os.path.isfile(filename):
            with open(filename) as file:
                lines = file.read()
            self.set_freqs(Nco.parse_nco(lines))
        elif filename:
            self.set_freqs(Nco.parse_nco(filename))
        else:
            pass
        self._lo1 = lo1
        self._lo2 = lo2

    @staticmethod
    def parse_nco(lines: str) -> list[float]:
        """
        Parse lines from a nco file. 

        Can only parse whole file at once.

        :param lines: lines in the file
        :type lines: str
        :raises AssertionError: if the format of the file is not correct.
        :raises ValueError: if frequency is not a floating-point number.
        :return: list of frequencies for this experiment
        :rtype: list[float]

        """
        lines = lines.split("\n")
        freqs = []
        # First line MUST be NCOPAR_VS	0.1
        assert lines[0].split() == ["NCOPAR_VS", "0.1"]
        for il, line in enumerate(lines[1:]):
            text = line.split("%")[0]
            if text.isspace():
                continue
            elems = text.split()
            assert len(elems) == 3
            assert elems[0] == "NCO"
            nr = int(elems[1])
            assert nr == len(freqs)
            # Assert that elem[2] is a floatin.point number
            # If this works, this is the fastest way ... If not, it should crash anyway.
            # https://stackoverflow.com/questions/354038/how-do-i-check-if-a-string-represents-a-number-float-or-int/23639915#23639915
            try:
                freq = float(elems[2])
            except ValueError:
                msg = f"{elems[2]} in line{il+2} is not a valid number!"
                raise ValueError(msg)

            freqs.append(freq)
        return freqs
    def set_freqs(self, freqs: list[float]) -> None:
        self.freqs = freqs

    def set_lo1(self, lo1: float) -> None:
        """
        Set local oscillator 1 frequency.
        
        :param lo1: Frequency [MHz]
        :type lo1: float

        """
        self._lo1 = lo1

    def set_lo2(self, lo2: float) -> None:
        """
        Set local oscillator 1 frequency.
        
        :param lo1: Frequency [MHz]
        :type lo1: float

        """
        self._lo2 = lo2

    def NCOSEL(self, nr: int) -> None:
        """
        Select frequency of numerical controlled oscillator.
        
        :param nr: Frequency number
        :type nr: int

        """
        self.f_nco = self.freqs[nr]

    def get_freq(self) -> float:
        """
        Return the centre frequency of this channel.
        
        :raises AttributeError: if frequency has not been selected
        :return: frequency [MHz]
        :rtype: float

        """
        return self._lo1 + self._lo2 - self.f_nco
